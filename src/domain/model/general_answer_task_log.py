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

    def add_attempt(self, response: str) -> None:
        """生成試行を記録（成功または失敗）"""
        self._attempts.append(
                GenerationAttempt(response=response)
            )

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

    def get_all_responses(self) -> list[str]:
        """すべての生成回答を取得"""
        return [attempt.response for attempt in self._attempts]

    def to_dict(self) -> dict:
        """State保存用の辞書に変換"""
        return {
            "type": "general_answer",
            "attempts": [
                {
                    "response": attempt.response
                }
                for attempt in self._attempts
            ]
        }

    @classmethod
    def from_dict(cls, data: dict) -> "GeneralAnswerTaskLog":
        """辞書からGeneralAnswerTaskLogを復元"""
        log = cls()

        for attempt_data in data.get("attempts", []):
            # GenerationAttemptを直接作成
            response = attempt_data.get("response", "")
            if response:
                attempt = GenerationAttempt(response=response)
                log._attempts.append(attempt)

        return log
