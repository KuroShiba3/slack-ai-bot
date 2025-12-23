from typing import Protocol

from .model import SearchResult


class SearchClient(Protocol):
    async def search(self, query: str, num_results: int = 3) -> list[SearchResult]:
        """検索クエリを実行し、検索結果を返す

        Args:
            query: 検索クエリ
            num_results: 取得する検索結果の数

        Returns:
            検索結果のリスト
        """
        ...
