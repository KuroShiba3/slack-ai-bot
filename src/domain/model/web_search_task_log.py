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

    def to_dict(self) -> dict[str, Any]:
        """辞書形式に変換"""
        return {
            "attempts": [
                {
                    "query": attempt.query,
                    "results": [
                        {
                            "url": result.url,
                            "title": result.title,
                            "content": result.content,
                        }
                        for result in attempt.results
                    ],
                }
                for attempt in self._attempts
            ]
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "WebSearchTaskLog":
        """辞書形式から復元"""
        task_log = cls.create()
        for attempt_data in data.get("attempts", []):
            results = [
                SearchResult(
                    url=r["url"],
                    title=r["title"],
                    content=r["content"],
                )
                for r in attempt_data.get("results", [])
            ]
            task_log._attempts.append(
                SearchAttempt(query=attempt_data["query"], results=results)
            )
        return task_log
