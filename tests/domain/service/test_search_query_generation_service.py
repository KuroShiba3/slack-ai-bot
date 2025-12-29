import pytest
from pydantic import BaseModel, Field
from pytest_mock import MockerFixture

from src.domain.model.task import Task
from src.domain.model.web_search_task_log import SearchResult
from src.domain.service.search_query_generation_service import (
    SearchQueryGenerationService,
)


@pytest.fixture
def mock_llm_client(mocker: MockerFixture):
    """LLMクライアントのモック"""
    return mocker.AsyncMock()


@pytest.fixture
def search_query_service(mock_llm_client):
    """SearchQueryGenerationServiceのインスタンス"""
    return SearchQueryGenerationService(llm_client=mock_llm_client)


@pytest.fixture
def web_search_task():
    """Web検索タスク"""
    return Task.create_web_search("Pythonの最新バージョンについて調べる")


@pytest.mark.asyncio
async def test_execute_generates_queries(
    search_query_service, mock_llm_client, web_search_task
):
    """検索クエリを生成するテスト"""

    class _SearchQueries(BaseModel):
        queries: list[str] = Field(
            description="生成された検索クエリのリスト(最大3個)", max_length=3
        )
        reason: str = Field(description="これらのクエリを選んだ理由")

    mock_llm_client.generate_with_structured_output.return_value = _SearchQueries(
        queries=["Python 最新バージョン", "Python 3.13 リリース"],
        reason="最新情報を得るため",
    )

    result = await search_query_service.execute(web_search_task)

    assert result == ["Python 最新バージョン", "Python 3.13 リリース"]
    assert mock_llm_client.generate_with_structured_output.called
    assert mock_llm_client.generate_with_structured_output.call_count == 1


@pytest.mark.asyncio
async def test_execute_includes_system_prompt(
    search_query_service, mock_llm_client, web_search_task
):
    """システムプロンプトが含まれることをテスト"""

    class _SearchQueries(BaseModel):
        queries: list[str] = Field(
            description="生成された検索クエリのリスト(最大3個)", max_length=3
        )
        reason: str = Field(description="これらのクエリを選んだ理由")

    mock_llm_client.generate_with_structured_output.return_value = _SearchQueries(
        queries=["クエリ1", "クエリ2"], reason="理由"
    )

    await search_query_service.execute(web_search_task)

    call_args = mock_llm_client.generate_with_structured_output.call_args
    messages = call_args[0][0]

    # 最初のメッセージがシステムプロンプトであることを確認
    assert messages[0].role.value == "system"
    assert "検索クエリ生成の専門家" in messages[0].content
    assert "複数の視点から検索" in messages[0].content


@pytest.mark.asyncio
async def test_execute_includes_task_description(
    search_query_service, mock_llm_client, web_search_task
):
    """タスクの説明が含まれることをテスト"""

    class _SearchQueries(BaseModel):
        queries: list[str] = Field(
            description="生成された検索クエリのリスト(最大3個)", max_length=3
        )
        reason: str = Field(description="これらのクエリを選んだ理由")

    mock_llm_client.generate_with_structured_output.return_value = _SearchQueries(
        queries=["クエリ"], reason="理由"
    )

    await search_query_service.execute(web_search_task)

    call_args = mock_llm_client.generate_with_structured_output.call_args
    messages = call_args[0][0]

    # 最後のメッセージにタスクの説明が含まれていることを確認
    last_message = messages[-1]
    assert "Pythonの最新バージョンについて調べる" in last_message.content
    assert "割り当てられたタスク" in last_message.content


@pytest.mark.asyncio
async def test_execute_includes_previous_queries_when_retry(
    search_query_service, mock_llm_client, web_search_task
):
    """前回の検索クエリが含まれることをテスト(リトライ時)"""

    class _SearchQueries(BaseModel):
        queries: list[str] = Field(
            description="生成された検索クエリのリスト(最大3個)", max_length=3
        )
        reason: str = Field(description="これらのクエリを選んだ理由")

    web_search_task.add_web_search_attempt(
        query="Python バージョン",
        results=[
            SearchResult(
                title="タイトル", url="https://example.com", content="コンテンツ"
            )
        ],
    )

    mock_llm_client.generate_with_structured_output.return_value = _SearchQueries(
        queries=["新しいクエリ"], reason="理由"
    )

    await search_query_service.execute(web_search_task)

    call_args = mock_llm_client.generate_with_structured_output.call_args
    messages = call_args[0][0]

    last_message = messages[-1]
    assert "すでに利用した検索クエリ" in last_message.content
    assert "Python バージョン" in last_message.content
    assert "異なる角度からの新しいクエリを生成してください" in last_message.content


@pytest.mark.asyncio
async def test_execute_includes_multiple_previous_queries(
    search_query_service, mock_llm_client, web_search_task
):
    """複数の前回検索クエリが含まれることをテスト"""

    class _SearchQueries(BaseModel):
        queries: list[str] = Field(
            description="生成された検索クエリのリスト(最大3個)", max_length=3
        )
        reason: str = Field(description="これらのクエリを選んだ理由")

    # 複数の検索履歴を追加
    web_search_task.add_web_search_attempt(
        query="Python バージョン",
        results=[
            SearchResult(
                title="タイトル1", url="https://example.com/1", content="コンテンツ1"
            )
        ],
    )
    web_search_task.add_web_search_attempt(
        query="Python 最新リリース",
        results=[
            SearchResult(
                title="タイトル2", url="https://example.com/2", content="コンテンツ2"
            )
        ],
    )

    mock_llm_client.generate_with_structured_output.return_value = _SearchQueries(
        queries=["新しいクエリ"], reason="理由"
    )

    await search_query_service.execute(web_search_task)

    call_args = mock_llm_client.generate_with_structured_output.call_args
    messages = call_args[0][0]

    last_message = messages[-1]
    assert "Python バージョン" in last_message.content
    assert "Python 最新リリース" in last_message.content


@pytest.mark.asyncio
async def test_execute_with_feedback(
    search_query_service, mock_llm_client, web_search_task
):
    """フィードバック付きで実行するテスト"""

    class _SearchQueries(BaseModel):
        queries: list[str] = Field(
            description="生成された検索クエリのリスト(最大3個)", max_length=3
        )
        reason: str = Field(description="これらのクエリを選んだ理由")

    mock_llm_client.generate_with_structured_output.return_value = _SearchQueries(
        queries=["改善されたクエリ"], reason="理由"
    )

    feedback = "もっと具体的な検索クエリにしてください"
    await search_query_service.execute(web_search_task, feedback=feedback)

    call_args = mock_llm_client.generate_with_structured_output.call_args
    messages = call_args[0][0]

    last_message = messages[-1]
    assert "改善フィードバック" in last_message.content
    assert feedback in last_message.content
    assert "上記のフィードバックを参考にしてください" in last_message.content


@pytest.mark.asyncio
async def test_execute_without_feedback(
    search_query_service, mock_llm_client, web_search_task
):
    """フィードバックなしで実行するテスト"""

    class _SearchQueries(BaseModel):
        queries: list[str] = Field(
            description="生成された検索クエリのリスト(最大3個)", max_length=3
        )
        reason: str = Field(description="これらのクエリを選んだ理由")

    mock_llm_client.generate_with_structured_output.return_value = _SearchQueries(
        queries=["クエリ"], reason="理由"
    )

    await search_query_service.execute(web_search_task, feedback=None)

    call_args = mock_llm_client.generate_with_structured_output.call_args
    messages = call_args[0][0]

    last_message = messages[-1]
    assert "改善フィードバック" not in last_message.content


@pytest.mark.asyncio
async def test_execute_with_previous_queries_and_feedback(
    search_query_service, mock_llm_client, web_search_task
):
    """前回クエリとフィードバックの両方がある場合のテスト"""

    class _SearchQueries(BaseModel):
        queries: list[str] = Field(
            description="生成された検索クエリのリスト(最大3個)", max_length=3
        )
        reason: str = Field(description="これらのクエリを選んだ理由")

    web_search_task.add_web_search_attempt(
        query="前回のクエリ",
        results=[
            SearchResult(
                title="タイトル", url="https://example.com", content="コンテンツ"
            )
        ],
    )

    mock_llm_client.generate_with_structured_output.return_value = _SearchQueries(
        queries=["改善されたクエリ"], reason="理由"
    )

    feedback = "より詳細な情報を検索してください"
    await search_query_service.execute(web_search_task, feedback=feedback)

    call_args = mock_llm_client.generate_with_structured_output.call_args
    messages = call_args[0][0]

    last_message = messages[-1]
    assert "すでに利用した検索クエリ" in last_message.content
    assert "前回のクエリ" in last_message.content
    assert "改善フィードバック" in last_message.content
    assert feedback in last_message.content


@pytest.mark.asyncio
async def test_execute_message_structure(
    search_query_service, mock_llm_client, web_search_task
):
    """メッセージ構造が正しいことをテスト"""

    class _SearchQueries(BaseModel):
        queries: list[str] = Field(
            description="生成された検索クエリのリスト(最大3個)", max_length=3
        )
        reason: str = Field(description="これらのクエリを選んだ理由")

    mock_llm_client.generate_with_structured_output.return_value = _SearchQueries(
        queries=["クエリ"], reason="理由"
    )

    await search_query_service.execute(web_search_task)

    call_args = mock_llm_client.generate_with_structured_output.call_args
    messages = call_args[0][0]

    # システムプロンプト(1) + ユーザープロンプト(1) = 2
    assert len(messages) == 2
    assert messages[0].role.value == "system"
    assert messages[1].role.value == "user"


@pytest.mark.asyncio
async def test_execute_uses_structured_output(
    search_query_service, mock_llm_client, web_search_task
):
    """構造化出力を使用することをテスト"""

    class _SearchQueries(BaseModel):
        queries: list[str] = Field(
            description="生成された検索クエリのリスト(最大3個)", max_length=3
        )
        reason: str = Field(description="これらのクエリを選んだ理由")

    mock_llm_client.generate_with_structured_output.return_value = _SearchQueries(
        queries=["クエリ1", "クエリ2", "クエリ3"], reason="3つの異なる視点から検索"
    )

    await search_query_service.execute(web_search_task)

    # generate_with_structured_outputが呼ばれたことを確認
    assert mock_llm_client.generate_with_structured_output.called
    # 通常のgenerateは呼ばれていないことを確認
    assert not mock_llm_client.generate.called


@pytest.mark.asyncio
async def test_execute_returns_only_queries(
    search_query_service, mock_llm_client, web_search_task
):
    """クエリのリストのみを返すことをテスト"""

    class _SearchQueries(BaseModel):
        queries: list[str] = Field(
            description="生成された検索クエリのリスト(最大3個)", max_length=3
        )
        reason: str = Field(description="これらのクエリを選んだ理由")

    mock_llm_client.generate_with_structured_output.return_value = _SearchQueries(
        queries=["クエリ1", "クエリ2"], reason="この理由は返り値に含まれない"
    )

    result = await search_query_service.execute(web_search_task)

    # reasonは含まれず、queriesのみが返されることを確認
    assert isinstance(result, list)
    assert result == ["クエリ1", "クエリ2"]


@pytest.mark.asyncio
async def test_build_human_prompt_format(search_query_service):
    """_build_human_promptが正しいフォーマットを生成することをテスト"""
    task_description = "Pythonの特徴を調べる"
    previous_queries = []
    feedback = None

    prompt = search_query_service._build_human_prompt(
        task_description, previous_queries, feedback
    )

    assert "## 現在の日付:" in prompt
    assert "## 割り当てられたタスク:" in prompt
    assert task_description in prompt


@pytest.mark.asyncio
async def test_build_human_prompt_with_previous_queries(search_query_service):
    """_build_human_promptが前回クエリを含むことをテスト"""
    task_description = "タスク"
    previous_queries = ["クエリ1", "クエリ2"]
    feedback = None

    prompt = search_query_service._build_human_prompt(
        task_description, previous_queries, feedback
    )

    assert "## すでに利用した検索クエリ:" in prompt
    assert "- クエリ1" in prompt
    assert "- クエリ2" in prompt
    assert "異なる角度からの新しいクエリを生成してください" in prompt


@pytest.mark.asyncio
async def test_build_human_prompt_with_feedback(search_query_service):
    """_build_human_promptがフィードバックを含むことをテスト"""
    task_description = "タスク"
    previous_queries = []
    feedback = "もっと具体的に"

    prompt = search_query_service._build_human_prompt(
        task_description, previous_queries, feedback
    )

    assert "## 改善フィードバック:" in prompt
    assert feedback in prompt
    assert "上記のフィードバックを参考にしてください" in prompt


@pytest.mark.asyncio
async def test_build_human_prompt_with_all_parameters(search_query_service):
    """_build_human_promptがすべてのパラメータを含むことをテスト"""
    task_description = "タスク"
    previous_queries = ["クエリ1"]
    feedback = "フィードバック"

    prompt = search_query_service._build_human_prompt(
        task_description, previous_queries, feedback
    )

    assert "## 現在の日付:" in prompt
    assert "## 割り当てられたタスク:" in prompt
    assert task_description in prompt
    assert "## すでに利用した検索クエリ:" in prompt
    assert "- クエリ1" in prompt
    assert "## 改善フィードバック:" in prompt
    assert feedback in prompt


@pytest.mark.asyncio
async def test_execute_with_general_answer_task(search_query_service, mock_llm_client):
    """一般回答タスクでも実行できることをテスト(前回クエリなし)"""

    class _SearchQueries(BaseModel):
        queries: list[str] = Field(
            description="生成された検索クエリのリスト(最大3個)", max_length=3
        )
        reason: str = Field(description="これらのクエリを選んだ理由")

    # 一般回答タスクを作成(WebSearchTaskLogを持たない)
    general_task = Task.create_general_answer("一般的な質問")

    mock_llm_client.generate_with_structured_output.return_value = _SearchQueries(
        queries=["クエリ"], reason="理由"
    )

    await search_query_service.execute(general_task)

    call_args = mock_llm_client.generate_with_structured_output.call_args
    messages = call_args[0][0]

    last_message = messages[-1]
    # 前回クエリのセクションが含まれないことを確認
    assert "すでに利用した検索クエリ" not in last_message.content
