import pytest

from src.domain.exception.task_log_exception import (
    EmptySearchQueryError,
    InvalidSearchResultsError,
)
from src.domain.model.web_search_task_log import (
    SearchAttempt,
    SearchResult,
    WebSearchTaskLog,
)


def test_create_empty_log():
    """空のタスクログを生成するテスト"""
    log = WebSearchTaskLog.create()

    assert log.attempts == []
    assert log.get_all_queries() == []


def test_add_single_attempt():
    """単一の検索試行を追加するテスト"""
    log = WebSearchTaskLog.create()
    query = "Python チュートリアル"
    results = [
        SearchResult(
            url="https://example.com/python",
            title="Python入門",
            content="Pythonの基本を学ぼう",
        )
    ]

    log.add_attempt(query=query, results=results)

    assert len(log.attempts) == 1
    assert log.attempts[0].query == query
    assert log.attempts[0].results == results
    assert log.get_all_queries() == [query]


def test_add_multiple_attempts():
    """複数の検索試行を追加するテスト"""
    log = WebSearchTaskLog.create()

    query1 = "Python"
    results1 = [
        SearchResult(url="https://example.com/1", title="Title 1", content="Content 1")
    ]

    query2 = "JavaScript"
    results2 = [
        SearchResult(url="https://example.com/2", title="Title 2", content="Content 2")
    ]

    log.add_attempt(query=query1, results=results1)
    log.add_attempt(query=query2, results=results2)

    assert len(log.attempts) == 2
    assert log.attempts[0].query == query1
    assert log.attempts[1].query == query2
    assert log.get_all_queries() == [query1, query2]


def test_add_attempt_with_multiple_results():
    """複数の検索結果を持つ試行を追加するテスト"""
    log = WebSearchTaskLog.create()
    query = "プログラミング言語"
    results = [
        SearchResult(url="https://example.com/1", title="Python", content="Content 1"),
        SearchResult(url="https://example.com/2", title="Java", content="Content 2"),
        SearchResult(
            url="https://example.com/3", title="JavaScript", content="Content 3"
        ),
    ]

    log.add_attempt(query=query, results=results)

    assert len(log.attempts) == 1
    assert len(log.attempts[0].results) == 3
    assert log.attempts[0].results[0].title == "Python"
    assert log.attempts[0].results[1].title == "Java"
    assert log.attempts[0].results[2].title == "JavaScript"


def test_to_dict_single_attempt():
    """単一試行のログを辞書に変換するテスト"""
    log = WebSearchTaskLog.create()
    query = "Python"
    results = [
        SearchResult(
            url="https://example.com/python",
            title="Python入門",
            content="Pythonの基本",
        )
    ]
    log.add_attempt(query=query, results=results)

    result = log.to_dict()

    assert result == {
        "attempts": [
            {
                "query": "Python",
                "results": [
                    {
                        "url": "https://example.com/python",
                        "title": "Python入門",
                        "content": "Pythonの基本",
                    }
                ],
            }
        ]
    }


def test_to_dict_multiple_attempts():
    """複数試行のログを辞書に変換するテスト"""
    log = WebSearchTaskLog.create()

    log.add_attempt(
        query="Python",
        results=[
            SearchResult(
                url="https://example.com/1", title="Title1", content="Content1"
            )
        ],
    )
    log.add_attempt(
        query="JavaScript",
        results=[
            SearchResult(
                url="https://example.com/2", title="Title2", content="Content2"
            )
        ],
    )

    result = log.to_dict()

    assert len(result["attempts"]) == 2
    assert result["attempts"][0]["query"] == "Python"
    assert result["attempts"][1]["query"] == "JavaScript"


def test_from_dict_single_attempt():
    """単一試行の辞書からログを復元するテスト"""
    data = {
        "attempts": [
            {
                "query": "Python",
                "results": [
                    {
                        "url": "https://example.com/python",
                        "title": "Python入門",
                        "content": "Pythonの基本",
                    }
                ],
            }
        ]
    }

    log = WebSearchTaskLog.from_dict(data)

    assert len(log.attempts) == 1
    assert log.attempts[0].query == "Python"
    assert len(log.attempts[0].results) == 1
    assert log.attempts[0].results[0].url == "https://example.com/python"
    assert log.attempts[0].results[0].title == "Python入門"
    assert log.attempts[0].results[0].content == "Pythonの基本"


def test_from_dict_multiple_attempts():
    """複数試行の辞書からログを復元するテスト"""
    data = {
        "attempts": [
            {
                "query": "Python",
                "results": [
                    {"url": "https://example.com/1", "title": "Title1", "content": "C1"}
                ],
            },
            {
                "query": "JavaScript",
                "results": [
                    {"url": "https://example.com/2", "title": "Title2", "content": "C2"}
                ],
            },
        ]
    }

    log = WebSearchTaskLog.from_dict(data)

    assert len(log.attempts) == 2
    assert log.attempts[0].query == "Python"
    assert log.attempts[1].query == "JavaScript"


def test_add_attempt_with_empty_query_raises_error():
    """空のクエリで試行を追加するとエラーになるテスト"""
    log = WebSearchTaskLog.create()
    results = [SearchResult(url="https://example.com", title="Test", content="Content")]

    with pytest.raises(EmptySearchQueryError, match="検索クエリが空です"):
        log.add_attempt(query="", results=results)


def test_add_attempt_with_whitespace_only_query_raises_error():
    """空白のみのクエリで試行を追加するとエラーになるテスト"""
    log = WebSearchTaskLog.create()
    results = [SearchResult(url="https://example.com", title="Test", content="Content")]

    with pytest.raises(EmptySearchQueryError, match="検索クエリが空です"):
        log.add_attempt(query="   ", results=results)


def test_add_attempt_with_empty_results_is_allowed():
    """空の検索結果は許容されるテスト"""
    log = WebSearchTaskLog.create()

    # 空の結果リストでも追加できる
    log.add_attempt(query="Python", results=[])

    assert len(log.attempts) == 1
    assert log.attempts[0].query == "Python"
    assert log.attempts[0].results == []


def test_add_attempt_with_none_results_raises_error():
    """None の検索結果を追加するとエラーになるテスト"""
    log = WebSearchTaskLog.create()

    with pytest.raises(InvalidSearchResultsError, match="検索結果がNoneです"):
        log.add_attempt(query="Python", results=None)
