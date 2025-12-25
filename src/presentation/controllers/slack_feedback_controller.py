import json
from typing import Any

from ...application.dto.feedback_usecase.feedback_input import (
    FeedbackInput,
)
from ...application.usecase.feedback_usecase import FeedbackUseCase
from ...log import get_logger

logger = get_logger(__name__)


class SlackFeedbackController:
    def __init__(self, feedback_usecase: FeedbackUseCase):
        self._feedback_usecase = feedback_usecase

    async def execute(self, ack, body: dict[str, Any]) -> None:
        try:
            await ack()

            if not self._validate_feedback_request(body):
                return

            action = body.get("actions", [{}])[0]
            value_data = json.loads(action.get("value", "{}"))

            message_id = value_data.get("message_id")
            feedback_type = value_data.get("type")
            user_id = body.get("user", {}).get("id")

            input_dto = FeedbackInput(
                message_id=message_id,
                feedback_type=feedback_type,
                user_id=user_id,
            )

            await self._feedback_usecase.execute(input_dto)

        except Exception as e:
            logger.error(f"フィードバック処理でエラーが発生しました: {e}", exc_info=True)

    def _validate_feedback_request(self, body: dict[str, Any]) -> bool:
        try:
            # 必須フィールドの存在チェック
            if not body or "actions" not in body or "user" not in body:
                logger.debug("必須フィールドが不足しています")
                return False

            actions = body.get("actions", [])
            if not actions or not isinstance(actions[0], dict):
                logger.debug("actionsが無効です")
                return False

            # action.valueのパースと検証
            action_value = actions[0].get("value")
            if not action_value:
                logger.debug("action.valueが存在しません")
                return False

            value_data = json.loads(action_value)

            # フィードバックデータの必須項目チェック
            if not all([
                value_data.get("message_id"),
                value_data.get("type"),
                body.get("user", {}).get("id")
            ]):
                logger.debug("フィードバックデータが不完全です")
                return False

            return True

        except (json.JSONDecodeError, KeyError, IndexError) as e:
            logger.debug(f"データ解析エラー: {str(e)}")
            return False