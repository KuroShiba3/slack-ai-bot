from dataclasses import dataclass

from .task_log import TaskLog

@dataclass
class GenerationAttempt:
    response: str

class GeneralAnswerTaskLog(TaskLog):
    def __init__(self):
        super().__init__()

    @property
    def response(self) -> str | None:
        """生成された回答を取得"""
        generation_attempts = [attempt for attempt in self._attempts if isinstance(attempt, GenerationAttempt)]
        if generation_attempts:
            return generation_attempts[-1].response
        return None