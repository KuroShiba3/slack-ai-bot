from dataclasses import dataclass, field
from typing import Dict, Any

@dataclass(frozen=True)
class AnswerToUserRequestInput:
    user_message: str
    context: Dict[str, Any] = field(default_factory=dict)