from typing import Any, Protocol


class TaskLog(Protocol):
    def add_attempt(self, **kwargs: Any) -> None:
        """試行をログに追加"""
        ...
