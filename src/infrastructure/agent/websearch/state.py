import operator
from typing import Annotated, TypedDict

from ...state.state import BaseState


class SearchResult(TypedDict):
    query: str
    title: str
    url: str
    snippet: str
    content: str | None

def merge_search_results(left: list[SearchResult] | None, right: list[SearchResult] | None) -> list[SearchResult]:
    """並列更新を許可しつつ、空リストでのクリアするリデューサー"""
    if right is None:
        return left or []
    if not right:
        return []
    if not left:
        return right
    return left + right

class PrivateState(TypedDict):
    task_id: str
    task_description: str
    task_result: str | None
    search_queries: Annotated[list[str], operator.add]
    search_results: Annotated[list[SearchResult], merge_search_results]
    feedback: str | None
    attempt: int
    completed: bool

class WebSearchState(BaseState, PrivateState):
    pass
