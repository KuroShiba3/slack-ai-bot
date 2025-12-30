from dataclasses import dataclass
from typing import Any

from src.domain.exception.task_log_exception import EmptyResponseError


@dataclass
class GenerationAttempt:
    response: str


class GeneralAnswerTaskLog:
    def __init__(self, attempts: list[GenerationAttempt]):
        self._attempts = attempts

    @classmethod
    def create(cls) -> "GeneralAnswerTaskLog":
        return cls(attempts=[])

    @classmethod
    def reconstruct(cls, attempts: list[GenerationAttempt]) -> "GeneralAnswerTaskLog":
        return cls(attempts=attempts)

    @property
    def attempts(self) -> list[GenerationAttempt]:
        """すべての試行を取得"""
        return self._attempts

    def add_attempt(self, response: str) -> None:
        """生成試行を記録"""
        if not response or not response.strip():
            raise EmptyResponseError()
        self._attempts.append(GenerationAttempt(response=response))

    def to_dict(self) -> dict[str, Any]:
        """辞書形式に変換"""
        return {
            "attempts": [{"response": attempt.response} for attempt in self._attempts]
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "GeneralAnswerTaskLog":
        """辞書形式から復元"""
        task_log = cls.create()
        for attempt_data in data.get("attempts", []):
            task_log._attempts.append(
                GenerationAttempt(response=attempt_data["response"])
            )
        return task_log
