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

    def add_attempt(self, query: str, results: list[SearchResult]) -> None:
        """検索試行を記録（成功または失敗）"""
        self._attempts.append(SearchAttempt(
            query=query,
            results=results
        ))

    @property
    def attempts(self) -> list[SearchAttempt]:
        """すべての試行を取得"""
        return self._attempts

    def get_all_queries(self) -> list[str]:
        """すべての検索クエリを取得"""
        return [attempt.query for attempt in self._attempts]

    def get_latest_results(self) -> list[SearchResult] | None:
        """最新の検索結果を取得"""
        if self._attempts:
            return self._attempts[-1].results
        return None

    def to_dict(self) -> dict:
        """State保存用の辞書に変換"""
        return {
            "type": "web_search",
            "attempts": [
                {
                    "query": attempt.query,
                    "results": [
                        {
                            "url": r.url,
                            "title": r.title,
                            "content": r.content
                        }
                        for r in attempt.results
                    ]
                }
                for attempt in self._attempts
            ]
        }

    @classmethod
    def from_dict(cls, data: dict) -> "WebSearchTaskLog":
        """辞書からWebSearchTaskLogを復元"""
        log = cls()

        for attempt_data in data.get("attempts", []):
            results = [
                SearchResult(
                    url=r["url"],
                    title=r["title"],
                    content=r["content"]
                )
                for r in attempt_data.get("results", [])
            ]
            # SearchAttemptを直接作成
            attempt = SearchAttempt(
                query=attempt_data["query"],
                results=results
            )
            log._attempts.append(attempt)

        return log
