from slack_sdk.web.async_client import AsyncWebClient

from .application.usecase.answer_to_user_request_usecase import (
    AnswerToUserRequestUseCase,
)
from .application.usecase.feedback_usecase import FeedbackUseCase
from .config import GOOGLE_API_KEY
from .infrastructure.external.llm import ModelFactory
from .infrastructure.external.slack import SlackMessageService
from .infrastructure.langgraph.graph.langgraph_workflow_service import LangGraphWorkflowService
from .infrastructure.repository.chat_session_repository import ChatSessionRepository
from .infrastructure.repository.feedback_repository import FeedbackRepository
from .presentation.controllers.slack_message_controller import SlackMessageController
from .presentation.controllers.slack_feedback_controller import SlackFeedbackController
from .presentation.mapper.slack_request_mapper import SlackRequestMapper


class DIContainer:
    """依存性注入コンテナ"""

    def __init__(self, slack_client: AsyncWebClient):
        # 環境変数のチェック
        if not GOOGLE_API_KEY:
            raise ValueError("GOOGLE_API_KEY環境変数が設定されていません")

        # インフラストラクチャ層
        self._model_factory = ModelFactory(google_api_key=GOOGLE_API_KEY)
        self._slack_service = SlackMessageService(slack_client=slack_client)
        self._chat_session_repository = ChatSessionRepository()
        self._feedback_repository = FeedbackRepository()

        # ドメイン層
        self._workflow_service = LangGraphWorkflowService(
            model_factory=self._model_factory
        )

        # アプリケーション層
        self._use_case = AnswerToUserRequestUseCase(
            workflow_service=self._workflow_service,
            chat_session_repository=self._chat_session_repository,
        )
        self._feedback_usecase = FeedbackUseCase(
            feedback_repository=self._feedback_repository,
        )

        # プレゼンテーション層
        self._mapper = SlackRequestMapper()
        self._controller = SlackMessageController(
            use_case=self._use_case,
            mapper=self._mapper,
            slack_service=self._slack_service,
        )
        self._feedback_controller = SlackFeedbackController(
            feedback_usecase=self._feedback_usecase,
        )

    @property
    def slack_message_controller(self) -> SlackMessageController:
        return self._controller

    @property
    def slack_feedback_controller(self) -> SlackFeedbackController:
        return self._feedback_controller

    @property
    def slack_message_service(self) -> SlackMessageService:
        return self._slack_service
