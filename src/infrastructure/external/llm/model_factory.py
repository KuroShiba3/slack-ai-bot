from typing import Any

from langchain_core.language_models import BaseChatModel
from langchain_google_genai import ChatGoogleGenerativeAI


class ModelFactory:
    def __init__(
        self,
        google_api_key: str,
        default_config: dict[str, Any] | None = None,
    ):
        self._google_api_key = google_api_key
        self._default_config = default_config or {"temperature": 0}

    def create(self, model_name: str) -> BaseChatModel:
        """指定されたモデルを生成"""
        if "gemini" in model_name.lower():
            return self._create_gemini(model_name)
        raise ValueError(f"不明なモデル名が指定されました: {model_name}")

    def _create_gemini(self, model_name: str) -> ChatGoogleGenerativeAI:
        return ChatGoogleGenerativeAI(
            model=model_name,
            google_api_key=self._google_api_key,
            **self._default_config,
        )
