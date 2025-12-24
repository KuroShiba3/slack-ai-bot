from abc import ABC, abstractmethod
from typing import Any


class TaskLog(ABC):
    @abstractmethod
    def add_attempt(self, **kwargs: Any) -> None:
        """試行をログに追加"""
        pass
