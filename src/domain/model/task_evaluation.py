from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class TaskEvaluation:
    is_satisfactory: bool
    need: Literal["search", "generate"] | None
    reason: str
    feedback: str | None
