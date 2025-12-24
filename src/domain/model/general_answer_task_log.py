from dataclasses import dataclass
from typing import Any


@dataclass
class GenerationAttempt:
    response: str


class GeneralAnswerTaskLog:
    def __init__(self, attempts: list[GenerationAttempt]):
        self._attempts = attempts

    @classmethod
    def create(cls) -> "GeneralAnswerTaskLog":
        return cls(attempts=[])

    @property
    def attempts(self) -> list[GenerationAttempt]:
        """すべての試行を取得"""
        return self._attempts

    def add_attempt(self, **kwargs: Any) -> None:
        """生成試行を記録"""
        response = kwargs.get("response")
        if response is not None:
            self._attempts.append(GenerationAttempt(response=response))
