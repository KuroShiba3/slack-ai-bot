from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class TaskEvaluation:
    """タスク結果の評価結果を表すドメイン値オブジェクト"""

    is_satisfactory: bool
    need: Literal["search", "generate"] | None
    reason: str
    feedback: str | None
