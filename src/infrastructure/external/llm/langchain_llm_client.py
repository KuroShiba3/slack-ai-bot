from typing import TypeVar

from pydantic import BaseModel

from ....domain.llm_client import LLMClient
from ....domain.model import Message
from ...langgraph.utils.message_converter import MessageConverter
from .model_factory import ModelFactory

T = TypeVar("T", bound=BaseModel)


class LangChainLLMClient(LLMClient):
    """LangChainを使用したLLMクライアント実装"""

    def __init__(
        self, model_factory: ModelFactory, default_model: str = "gemini-2.0-flash"
    ):
        self._model_factory = model_factory
        self._default_model = default_model

    async def generate(self, messages: list[Message]) -> str:
        """メッセージリストから通常のテキスト生成を行う

        Args:
            messages: メッセージリスト

        Returns:
            生成されたテキスト
        """
        # ドメインのMessageをLangChainのメッセージに変換
        langchain_messages = MessageConverter.to_langchain_messages(messages)

        # モデルを作成して生成
        model = self._model_factory.create(self._default_model)
        response = await model.ainvoke(langchain_messages)

        return response.content

    async def generate_with_structured_output(
        self, messages: list[Message], response_model: type[T]
    ) -> T:
        """メッセージリストから構造化された出力を生成する

        Args:
            messages: メッセージリスト
            response_model: 出力のPydanticモデル

        Returns:
            構造化された出力
        """
        # ドメインのMessageをLangChainのメッセージに変換
        langchain_messages = MessageConverter.to_langchain_messages(messages)

        # モデルを作成して構造化出力
        model = self._model_factory.create(self._default_model)
        structured_model = model.with_structured_output(response_model)
        return await structured_model.ainvoke(langchain_messages)
