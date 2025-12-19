from abc import ABC, abstractmethod


class TaskLog(ABC):
    @abstractmethod
    def to_dict(self) -> dict:
        """State保存用の辞書に変換"""
        pass

    @classmethod
    @abstractmethod
    def from_dict(cls, data: dict) -> "TaskLog":
        """辞書からTaskLogを復元"""
        pass