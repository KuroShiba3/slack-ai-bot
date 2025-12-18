from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class AnswerToUserRequestInput:
    user_message: str
    context: dict[str, Any] = field(default_factory=dict)
