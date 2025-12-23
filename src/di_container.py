"""依存性注入コンテナ"""
from slack_sdk.web.async_client import AsyncWebClient

from .application.usecase.answer_to_user_request_usecase import AnswerToUserRequestUseCase
from .infrastructure.repository.in_memory_chat_session_repository import InMemoryChatSessionRepository
from .infrastructure.langgraph.graph.workflow_service import LangGraphWorkflowService
from .infrastructure.external.llm import ModelFactory
from .infrastructure.external.slack import SlackMessageService
from .presentation.controllers.slack_message_controller import SlackMessageController
from .presentation.mapper.slack_request_mapper import SlackRequestMapper
from .config import GOOGLE_API_KEY


class DIContainer:
    """依存性注入コンテナ"""

    def __init__(self, slack_client: AsyncWebClient):
        # インフラストラクチャ層
        self._model_factory = ModelFactory(google_api_key=GOOGLE_API_KEY)
        self._slack_service = SlackMessageService(slack_client=slack_client)
        self._chat_session_repository = InMemoryChatSessionRepository()

        # ドメイン層
        self._workflow_service = LangGraphWorkflowService(
            model_factory=self._model_factory,
            model_name="gemini-2.0-flash"
        )

        # アプリケーション層
        self._use_case = AnswerToUserRequestUseCase(
            workflow_service=self._workflow_service,
            chat_session_repository=self._chat_session_repository
        )

        # プレゼンテーション層
        self._mapper = SlackRequestMapper()
        self._controller = SlackMessageController(
            use_case=self._use_case,
            mapper=self._mapper,
            slack_service=self._slack_service
        )

    @property
    def slack_message_controller(self) -> SlackMessageController:
        return self._controller

    @property
    def slack_message_service(self) -> SlackMessageService:
        return self._slack_service
