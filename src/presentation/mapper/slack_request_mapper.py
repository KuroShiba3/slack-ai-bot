import re
from typing import Any

from ...application.dto.answer_to_user_request_usecase.answer_to_user_request_input import (
    AnswerToUserRequestInput,
)
from ..dto.slack_request_dto import SlackRequestDTO
from ..exception.request_exception import InvalidRequestError


class SlackRequestMapper:
    @staticmethod
    def from_event(event: dict[str, Any]) -> SlackRequestDTO:
        """SlackイベントからDTOを生成"""
        required_fields = {
            "text": "テキスト",
            "user": "ユーザーID",
            "channel": "チャンネルID",
            "ts": "タイムスタンプ",
            "event_ts": "イベントタイムスタンプ",
        }

        for field, name in required_fields.items():
            if not event.get(field):
                raise InvalidRequestError(f"{name}({field})")

        # テキストの空チェック
        text = SlackRequestMapper._remove_mention(event.get("text", ""))
        if not text.strip():
            raise InvalidRequestError("text(空のメッセージ)")

        # ユーザーIDの形式チェック
        user_id = event.get("user", "")
        if not user_id.startswith("U"):
            raise InvalidRequestError(f"user(不正な形式: {user_id})")

        # チャンネルIDの形式チェック
        channel_id = event.get("channel", "")
        if not any(channel_id.startswith(prefix) for prefix in ["C", "D", "G"]):
            raise InvalidRequestError(f"channel(不正な形式: {channel_id})")

        return SlackRequestDTO(
            text=text,
            user_id=user_id,
            channel_id=channel_id,
            message_ts=event["ts"],
            thread_ts=event.get("thread_ts"),
            event_id=event["event_ts"],
            bot_id=event.get("bot_id"),
        )

    @staticmethod
    def to_application_input(slack_dto: SlackRequestDTO) -> AnswerToUserRequestInput:
        """SlackDTOをアプリケーション層のDTOに変換"""
        return AnswerToUserRequestInput(
            user_message=slack_dto.text,
            context={
                "user_id": slack_dto.user_id,
                "channel_id": slack_dto.channel_id,
                "thread_ts": slack_dto.thread_ts,
                "message_ts": slack_dto.message_ts,
                "conversation_id": f"{slack_dto.channel_id}_{slack_dto.thread_ts}",
            },
        )

    @staticmethod
    def is_bot_message(slack_dto: SlackRequestDTO) -> bool:
        """ボットメッセージかどうかを判定"""
        return bool(slack_dto.bot_id)

    @staticmethod
    def _remove_mention(text: str) -> str:
        """メンション部分を削除してテキストをクリーンアップ"""
        return re.sub(r"<@[A-Z0-9]+>", "", text).strip()
