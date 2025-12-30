from typing import TypeVar

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from pydantic import BaseModel

from src.infrastructure.exception.llm_exception import UnsupportedMessageRoleError

from ....domain.model import Message, Role
from ....domain.service.port.llm_client import LLMClient
from .model_factory import ModelFactory

T = TypeVar("T", bound=BaseModel)


class LangChainLLMClient(LLMClient):
    def __init__(
        self, model_factory: ModelFactory, model_name: str = "gemini-2.0-flash"
    ):
        self._model_factory = model_factory
        self._model_name = model_name

    def _to_langchain_messages(self, messages: list[Message]) -> list[BaseMessage]:
        """ドメインモデルのMessageをLangChainのメッセージに変換"""
        langchain_messages: list[BaseMessage] = []

        for msg in messages:
            if msg.role == Role.USER:
                langchain_messages.append(HumanMessage(content=msg.content))
            elif msg.role == Role.ASSISTANT:
                langchain_messages.append(AIMessage(content=msg.content))
            elif msg.role == Role.SYSTEM:
                langchain_messages.append(SystemMessage(content=msg.content))
            else:
                raise UnsupportedMessageRoleError(msg.role.value)

        return langchain_messages

    async def generate(self, messages: list[Message]) -> str:
        """メッセージリストから通常のテキスト生成を行う"""
        langchain_messages = self._to_langchain_messages(messages)

        model = self._model_factory.create(self._model_name)
        response = await model.ainvoke(langchain_messages)

        return response.content  # type: ignore

    async def generate_with_structured_output(
        self, messages: list[Message], response_model: type[T]
    ) -> T:
        """メッセージリストから構造化された出力を生成する"""
        langchain_messages = self._to_langchain_messages(messages)

        model = self._model_factory.create(self._model_name)
        structured_model = model.with_structured_output(response_model)
        return await structured_model.ainvoke(langchain_messages)  # type: ignore
