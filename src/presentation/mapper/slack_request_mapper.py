import re
from typing import Dict, Any
from ..dto.slack_request_dto import SlackRequestDTO
from ...application.dto.answer_to_user_request_usecase.answer_to_user_request_input import AnswerToUserRequestInput


class SlackRequestMapper:
    """Slackリクエストの変換を担当するマッパー"""

    @staticmethod
    def from_event(event: Dict[str, Any]) -> SlackRequestDTO:
        """SlackイベントからDTOを生成"""
        text = SlackRequestMapper._remove_mention(event.get('text', ''))

        return SlackRequestDTO(
            text=text,
            user_id=event.get('user_id', ''),
            channel_id=event.get('channel_id', ''),
            thread_ts=event.get('thread_ts'),
            message_ts=event.get('ts'),
            event_id=event.get('event_id'),
            bot_id=event.get('bot_id')
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
                "conversation_id": f"{slack_dto.channel_id}_{slack_dto.thread_ts}"
            }
        )

    @staticmethod
    def is_bot_message(slack_dto: SlackRequestDTO) -> bool:
        """ボットメッセージかどうかを判定"""
        return bool(slack_dto.bot_id)

    @staticmethod
    def _remove_mention(text: str) -> str:
        """メンション部分を削除してテキストをクリーンアップ"""
        return re.sub(r'<@[A-Z0-9]+>', '', text).strip()