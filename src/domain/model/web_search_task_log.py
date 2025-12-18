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
    def __init__(self):
        super().__init__()

    def get_all_queries(self) -> list[str]:
        """すべての検索クエリを取得"""
        return [attempt.query for attempt in self._attempts if isinstance(attempt, SearchAttempt)]
