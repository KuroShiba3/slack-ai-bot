from typing import Any, Protocol


class TaskLog(Protocol):
    def add_attempt(self, **kwargs: Any) -> None:
        """試行をログに追加"""
        ...

    def to_dict(self) -> dict[str, Any]:
        """辞書形式に変換"""
        ...

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TaskLog":
        """辞書形式から復元"""
        ...
