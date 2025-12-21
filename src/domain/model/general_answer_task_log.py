from dataclasses import dataclass

from .task_log import TaskLog


@dataclass
class GenerationAttempt:
    response: str

class GeneralAnswerTaskLog(TaskLog):
    def __init__(self, attempts: list[GenerationAttempt]):
        self._attempts = attempts

    @classmethod
    def create(cls) -> "GeneralAnswerTaskLog":
        return cls(attempts=[])

    @property
    def attempts(self) -> list[GenerationAttempt]:
        """すべての試行を取得"""
        return self._attempts

    @property
    def response(self) -> str | None:
        """最新の生成された回答を取得"""
        if self._attempts:
            return self._attempts[-1].response
        return None

    def add_attempt(self, response: str) -> None:
        """生成試行を記録"""
        self._attempts.append(
                GenerationAttempt(response=response)
            )