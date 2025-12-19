from dataclasses import dataclass


@dataclass(frozen=True)
class AnswerToUserRequestOutput:
    answer: str
    message_id: str
