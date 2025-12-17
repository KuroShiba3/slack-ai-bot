from abc import ABC
from datetime import datetime
from typing import Any

class TaskLog(ABC):
    def __init__(self):
        self._retry_count = 0
        self._max_retries = 3
        self._started_at: datetime | None = None
        self._completed_at: datetime | None = None
        self._error_messages: list[str] = []
        self._attempts: list[Any] = []

    def mark_started(self) -> None:
        """作業開始を記録"""
        self._started_at = datetime.now()

    def mark_completed(self) -> None:
        """作業完了を記録"""
        self._completed_at = datetime.now()

    def mark_failed(self, error: str) -> None:
        """作業失敗を記録"""
        self._error_messages.append(error)
        self._completed_at = datetime.now()

    def can_retry(self) -> bool:
        """リトライ可能か判定"""
        return self._retry_count < self._max_retries

    def increment_retry(self) -> None:
        """リトライ回数を増加"""
        self._retry_count += 1

    def add_attempt(self, attempt: Any) -> None:
        """試行を追加"""
        self._attempts.append(attempt)

    @property
    def attempts(self) -> list[Any]:
        """全ての試行を取得"""
        return self._attempts

    @property
    def is_completed(self) -> bool:
        """完了済みか判定"""
        return self._completed_at is not None