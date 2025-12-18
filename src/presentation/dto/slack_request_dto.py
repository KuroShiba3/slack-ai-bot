from dataclasses import dataclass


@dataclass(frozen=True)
class SlackRequestDTO:
    """Slack固有のリクエストDTO(純粋なデータ構造)"""
    text: str
    user_id: str
    channel_id: str
    thread_ts: str | None = None
    message_ts: str | None = None
    team_id: str | None = None
    event_id: str | None = None
    bot_id: str | None = None
