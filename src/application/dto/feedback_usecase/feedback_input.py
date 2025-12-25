from dataclasses import dataclass


@dataclass(frozen=True)
class FeedbackInput:
    message_id: str
    feedback_type: str  # "good" or "bad"
    user_id: str