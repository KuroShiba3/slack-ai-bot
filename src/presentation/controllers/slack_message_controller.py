from typing import Any

from slack_bolt.async_app import AsyncAck

from ...application.exception.base import ApplicationException
from ...application.usecase.answer_to_user_request_usecase import (
    AnswerToUserRequestUseCase,
)
from ...domain.exception.base import DomainException
from ...infrastructure.exception.base import InfrastructureException
from ...infrastructure.external.slack.slack_message_service import SlackMessageService
from ...log.logger import get_logger
from ..dto.slack_request_dto import SlackRequestDTO
from ..exception.base import PresentationException
from ..mapper import SlackRequestMapper

logger = get_logger(__name__)


class SlackMessageController:
    _processed_events: set[str] = set()

    def __init__(
        self,
        use_case: AnswerToUserRequestUseCase,
        mapper: SlackRequestMapper,
        slack_service: SlackMessageService,
    ):
        self._use_case = use_case
        self._mapper = mapper
        self._slack_service = slack_service

    async def execute(self, ack: AsyncAck, body: dict[str, Any]) -> None:
        await ack()

        event = body.get("event", {})
        try:
            # Mapperがバリデーションを行う（検証済みDTOを返す）
            slack_dto = self._mapper.from_event(event)
            # 重複チェック
            if slack_dto.event_id in self._processed_events:
                logger.debug(
                    f"重複したイベントをスキップしました: {slack_dto.event_id}"
                )
                return
            self._processed_events.add(slack_dto.event_id)

            # ボットメッセージチェック
            if self._mapper.is_bot_message(slack_dto):
                logger.debug("ボットメッセージを無視します")
                return

            # リアクション追加
            await self._slack_service.add_reaction(
                slack_dto.channel_id, slack_dto.message_ts, "eyes"
            )

            input_dto = self._mapper.to_application_input(slack_dto)

            # ユースケース実行
            output_dto = await self._use_case.execute(input_dto)

            await self._slack_service.send_message(
                channel=event.get("channel"),
                text=output_dto.answer,
                thread_ts=slack_dto.thread_ts or slack_dto.message_ts,
                message_id=output_dto.message_id,
            )

            # リアクション削除
            await self._slack_service.remove_reaction(
                slack_dto.channel_id, slack_dto.message_ts, "eyes"
            )

        except PresentationException as e:
            logger.error(f"リクエストエラー: {e.message}")

        except ApplicationException as e:
            logger.error(f"入力エラー: {e.message}")

        except (DomainException, InfrastructureException) as e:
            logger.error(f"システムエラー: {e.message}", exc_info=True)
            if "slack_dto" in locals():
                await self._handle_error_response(
                    event,
                    slack_dto,
                    "システムエラーが発生しました。新しいスレッドで再度お試しください。",
                )
            raise e

        except Exception as e:
            logger.critical(f"予期しないエラー: {e}", exc_info=True)
            if "slack_dto" in locals():
                await self._handle_error_response(
                    event,
                    slack_dto,
                    "予期しないエラーが発生しました。新しいスレッドで再度お試しください。",
                )
            raise e

    async def _handle_error_response(
        self, event: dict[str, Any], slack_dto: SlackRequestDTO, message: str
    ) -> None:
        """エラーレスポンスを処理"""
        # リアクション削除
        try:
            await self._slack_service.remove_reaction(
                slack_dto.channel_id, slack_dto.message_ts, "eyes"
            )
        except Exception as e:
            logger.warning(f"リアクション削除に失敗: {e}")

        # エラーメッセージ送信
        await self._slack_service.send_message(
            channel=event.get("channel"),
            text=message,
            thread_ts=slack_dto.thread_ts or slack_dto.message_ts,
            use_blocks=False,
        )
