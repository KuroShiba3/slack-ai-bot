from dataclasses import dataclass


@dataclass(frozen=True)
class SlackRequestDTO:
    text: str
    user_id: str
    channel_id: str
    event_id: str
    message_ts: str
    thread_ts: str | None = None
    team_id: str | None = None
    bot_id: str | None = None
