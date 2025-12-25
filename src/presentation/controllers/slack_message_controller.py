from typing import Any

from slack_bolt.async_app import AsyncAck

from ...application.usecase.answer_to_user_request_usecase import (
    AnswerToUserRequestUseCase,
)
from ...infrastructure.external.slack.slack_message_service import SlackMessageService
from ...log.logger import get_logger
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

        if not self._validate_event(event):
            return

        slack_dto = self._mapper.from_event(event)
        if slack_dto.event_id and slack_dto.event_id in self._processed_events:
            logger.debug(f"重複したイベントをスキップしました: {slack_dto.event_id}")
            return
        if slack_dto.event_id:
            self._processed_events.add(slack_dto.event_id)

        if self._mapper.is_bot_message(slack_dto):
            logger.debug("ボットメッセージを無視します")
            return

        try:
            if slack_dto.channel_id and slack_dto.message_ts:
                await self._slack_service.add_reaction(
                    slack_dto.channel_id, slack_dto.message_ts, "eyes"
                )

            input_dto = self._mapper.to_application_input(slack_dto)
            logger.debug(f"ユーザーからのメッセージを受信しました: {input_dto.user_message}")

            output_dto = await self._use_case.execute(input_dto)
            logger.debug(f"生成された回答: {output_dto.answer}")

            await self._slack_service.send_message(
                channel=event.get("channel"),
                text=output_dto.answer,
                thread_ts=slack_dto.thread_ts or slack_dto.message_ts,
                message_id=output_dto.message_id,
            )

            if slack_dto.channel_id and slack_dto.message_ts:
                await self._slack_service.remove_reaction(
                    slack_dto.channel_id, slack_dto.message_ts, "eyes"
                )
        except Exception as e:
            logger.error(f"メッセージ処理でエラーが発生しました: {e}")

            await self._slack_service.send_message(
                channel=event.get("channel"),
                text="エラーが発生しました。新しいスレッドで再度お試しください。",
                thread_ts=slack_dto.thread_ts or slack_dto.message_ts,
                use_blocks=False,
            )

    def _validate_event(self, event: dict[str, Any]) -> bool:
        # 必須フィールドのチェック
        required_fields = ["text", "user", "channel"]

        for field in required_fields:
            if field not in event or not event[field]:
                logger.error(f"必須フィールド '{field}' が存在しないか空です")
                return False

        # textが空文字列でないことを確認
        text = event.get("text", "").strip()
        if not text:
            logger.debug("空のメッセージを受信しました")
            return False

        # 推奨フィールドのチェック
        if "ts" not in event:
            logger.warning("タイムスタンプ(ts)が存在しません")

        if "event_ts" not in event:
            logger.warning("イベントタイムスタンプ(event_ts)が存在しません")

        # ユーザーIDの形式チェック
        user_id = event.get("user", "")
        if not user_id.startswith("U"):
            logger.warning(f"不正なユーザーID形式: {user_id}")

        # チャンネルIDの形式チェック
        channel_id = event.get("channel", "")
        if not any(channel_id.startswith(prefix) for prefix in ["C", "D", "G"]):
            logger.warning(f"不正なチャンネルID形式: {channel_id}")

        return True
