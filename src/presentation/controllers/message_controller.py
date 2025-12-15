from dataclasses import dataclass
from typing import List, Dict, Any, Optional

from slack_bolt.async_app import AsyncAck
from slack_bolt.request.async_request import AsyncBoltRequest

from ...log.logger import get_logger

logger = get_logger(__name__)

@dataclass
class SlackMessageRequest:
    event_id: str
    bot_id: Optional[str]
    user_id: str
    channel_id: str
    message_ts: str
    thread_ts: str
    text: str

    @classmethod
    def from_event(cls, request: Dict[str, Any]) -> "SlackMessageRequest":
        event = request.get('event', {})

        return cls(
            event_id=event.get('event_id'),
            bot_id=event.get('bot_id'),
            user_id=event.get('user_id', ''),
            channel_id=event.get('channel_id', ''),
            message_ts=event.get('ts', ''),
            thread_ts=event.get('thread_ts', event.get('ts', '')),
            text=event.get('text', '')
        )

    def is_bot_message(self) -> bool:
        return bool(self.bot_id)

class MessageController:
    def __init__(self, use_case=None):
        self.use_case = use_case
        self.processed_events = set()

    async def exec(self, ack: AsyncAck, request: AsyncBoltRequest) -> Optional[str]:
        slack_massage_request = SlackMessageRequest.from_event(request.body)

        if slack_massage_request.event_id in self.processed_events:
            logger.info(f"重複したイベントをスキップしました。: {slack_massage_request.event_id}")
            return
        self.processed_events.add(slack_massage_request.event_id)

        if slack_massage_request.is_bot_message():
            logger.info("botメッセージを無視します。")
            return

        self.use_case.exec()