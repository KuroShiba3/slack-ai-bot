from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class SlackRequestDTO:
    """Slack固有のリクエストDTO（純粋なデータ構造）"""
    text: str
    user_id: str
    channel_id: str
    thread_ts: Optional[str] = None
    message_ts: Optional[str] = None
    team_id: Optional[str] = None
    event_id: Optional[str] = None
    bot_id: Optional[str] = None