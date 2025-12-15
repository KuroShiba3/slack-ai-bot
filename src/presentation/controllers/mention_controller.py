from dataclasses import dataclass
from typing import Dict, Any, Optional

from slack_bolt.async_app import AsyncAck

from ...log.logger import get_logger

logger = get_logger(__name__)

@dataclass
class SlackMentionRequest:
    bot_id: Optional[str]
    text: str
    ts: str
    channel: str

    @classmethod
    def from_event(cls, event: Dict[str, Any]) -> "SlackMentionRequest":
        return cls(
            event_id=event.get('event_id'),
            event=event.get('event', {}),
            bot_id=event.get('bot_id', ''),
            user_id=event.get('user_id', ''),
            channel_id=event.get('channel_id', ''),
            message_ts=event.get('ts', ''),
            thread_ts=event.get('thread_ts', event.get('ts', '')),
            text=event.get('text', '')
        )

class MentionController:
    def __init__(self, use_case=None):
        self.use_case = use_case
        self.processed_events = set()

    async def exec(self, ack: AsyncAck, request: SlackMentionRequest) -> Optional[str]:
        print(type(ack))