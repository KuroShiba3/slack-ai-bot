from typing import Protocol

from ....domain.model import SearchResult


class SearchClient(Protocol):
    async def search(self, query: str, num_results: int = 3) -> list[SearchResult]:
        ...
