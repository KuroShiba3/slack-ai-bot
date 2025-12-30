import json
from typing import Any

from ...application.dto.feedback_usecase import FeedbackInput
from ...application.exception.base import ApplicationException
from ...application.usecase import FeedbackUseCase
from ...domain.exception.base import DomainException
from ...infrastructure.exception.base import InfrastructureException
from ...log import get_logger
from ..exception.base import PresentationException
from ..exception.request_exception import InvalidRequestError

logger = get_logger(__name__)


class SlackFeedbackController:
    def __init__(self, feedback_usecase: FeedbackUseCase):
        self._feedback_usecase = feedback_usecase

    async def execute(self, ack, body: dict[str, Any]) -> None:
        await ack()

        try:
            # フィードバックリクエストを解析・検証
            input_dto = self._parse_feedback_request(body)

            # UseCaseを実行
            await self._feedback_usecase.execute(input_dto)

        except PresentationException as e:
            logger.error(f"フィードバックリクエストエラー: {e.message}")

        except ApplicationException as e:
            logger.error(f"フィードバック入力エラー: {e.message}")

        except (DomainException, InfrastructureException) as e:
            logger.error(
                f"フィードバック処理でシステムエラー: {e.message}", exc_info=True
            )
            raise e

        except Exception as e:
            logger.critical(f"フィードバック処理で予期しないエラー: {e}", exc_info=True)
            raise e

    def _parse_feedback_request(self, body: dict[str, Any]) -> FeedbackInput:
        """Slackフィードバックリクエストを解析・検証してDTOを生成"""
        try:
            if not body:
                raise InvalidRequestError("body(リクエストボディが空)")

            if "actions" not in body:
                raise InvalidRequestError("actions(フィールドが存在しない)")

            if "user" not in body:
                raise InvalidRequestError("user(フィールドが存在しない)")

            actions = body.get("actions", [])
            if not actions or not isinstance(actions, list) or len(actions) == 0:
                raise InvalidRequestError("actions(配列が空または不正)")

            # action.valueのパースと検証
            action = actions[0]
            if not isinstance(action, dict):
                raise InvalidRequestError("actions[0](不正な型)")

            action_value = action.get("value")
            if not action_value:
                raise InvalidRequestError("action.value(存在しない)")

            # JSONパース
            value_data = json.loads(action_value)

            # 必須項目の抽出と検証
            message_id = value_data.get("message_id")
            if not message_id:
                raise InvalidRequestError("message_id(action.valueに存在しない)")

            feedback_type = value_data.get("type")
            if not feedback_type:
                raise InvalidRequestError("type(action.valueに存在しない)")

            user_id = body.get("user", {}).get("id")
            if not user_id:
                raise InvalidRequestError("user.id(存在しない)")

            return FeedbackInput(
                message_id=message_id,
                feedback_type=feedback_type,
                user_id=user_id,
            )

        except json.JSONDecodeError as e:
            raise InvalidRequestError(f"action.value(JSON解析エラー: {e})") from e
        except (KeyError, TypeError, IndexError) as e:
            raise InvalidRequestError(f"リクエスト構造エラー: {e}") from e
