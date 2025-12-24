from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class SearchResult:
    url: str
    title: str
    content: str


@dataclass
class SearchAttempt:
    query: str
    results: list[SearchResult]


class WebSearchTaskLog:
    def __init__(self, attempts: list[SearchAttempt]):
        self._attempts = attempts

    @classmethod
    def create(cls) -> "WebSearchTaskLog":
        return cls(attempts=[])

    @property
    def attempts(self) -> list[SearchAttempt]:
        """すべての試行を取得"""
        return self._attempts

    def add_attempt(self, **kwargs: Any) -> None:
        """検索試行を記録"""
        query = kwargs.get("query")
        results = kwargs.get("results")
        if query is not None and results is not None:
            self._attempts.append(SearchAttempt(query=query, results=results))

    def get_all_queries(self) -> list[str]:
        """すべての検索クエリを取得"""
        return [attempt.query for attempt in self._attempts]
