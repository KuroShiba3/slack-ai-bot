from typing import Protocol, TypeVar

from pydantic import BaseModel

from ...model import Message

T = TypeVar("T", bound=BaseModel)


class LLMClient(Protocol):
    async def generate(self, messages: list[Message]) -> str:
        """メッセージリストから通常のテキスト生成を行う"""
        ...

    async def generate_with_structured_output(
        self, messages: list[Message], response_model: type[T]
    ) -> T:
        """メッセージリストから構造化された出力を生成する"""
        ...
