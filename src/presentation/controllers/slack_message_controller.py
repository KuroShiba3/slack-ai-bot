from typing import Any, Optional

from slack_bolt.async_app import AsyncAck

from ...application.usecase.answer_to_user_request_usecase import (
    AnswerToUserRequestUseCase,
)
from ...infrastructure.slack.slack_message_service import SlackMessageService
from ...log.logger import get_logger
from ..mapper.slack_request_mapper import SlackRequestMapper

logger = get_logger(__name__)

class SlackMessageController:
    def __init__(
        self,
        use_case: AnswerToUserRequestUseCase,
        mapper: SlackRequestMapper,
        slack_service: SlackMessageService,
    ):
        self._use_case = use_case
        self._mapper = mapper
        self._slack_service = slack_service
        self._processed_events = set()

    async def execute(self, ack: AsyncAck, body: dict[str, Any], say) -> None:
        """Slackのメッセージイベントを処理"""
        await ack()

        event = body.get('event', {})
        slack_dto = self._mapper.from_event(event)

        if slack_dto.event_id in self._processed_events:
            logger.debug(f"重複したイベントをスキップしました: {slack_dto.event_id}")
            return
        self._processed_events.add(slack_dto.event_id)

        if self._mapper.is_bot_message(slack_dto):
            logger.debug("ボットメッセージを無視します")
            return

        try:
            await self._slack_service.add_reaction(slack_dto.channel_id, slack_dto.message_ts, "eyes")

            input_dto = self._mapper.to_application_input(slack_dto)
            output_dto = await self._use_case.execute(input_dto)

            await self._slack_service.send_message(
                    channel=event.get("channel"),
                    text=output_dto.answer,
                    thread_ts=slack_dto.thread_ts or slack_dto.message_ts,
                    message_id=output_dto.message_id,
                )
        except Exception as e:
            logger.error(f"メッセージ処理でエラーが発生しました: {e}")

            await self._slack_service.send_message(
                    channel=event.get("channel"),
                    text="申し訳ありません。エラーが発生しました。",
                    thread_ts=slack_dto.thread_ts or slack_dto.message_ts,
                    use_blocks=False,
                )