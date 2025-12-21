from dataclasses import dataclass

from .task_log import TaskLog


@dataclass(frozen=True)
class SearchResult:
    url: str
    title: str
    content: str

@dataclass
class SearchAttempt:
    query: str
    results: list[SearchResult]

class WebSearchTaskLog(TaskLog):
    def __init__(self, attempts: list[SearchAttempt]):
        self._attempts = attempts

    @classmethod
    def create(cls) -> "WebSearchTaskLog":
        return cls(attempts=[])

    @property
    def attempts(self) -> list[SearchAttempt]:
        """すべての試行を取得"""
        return self._attempts

    def add_attempt(self, query: str, results: list[SearchResult]) -> None:
        """検索試行を記録"""
        self._attempts.append(SearchAttempt(
            query=query,
            results=results
        ))

    def get_all_queries(self) -> list[str]:
        """すべての検索クエリを取得"""
        return [attempt.query for attempt in self._attempts]