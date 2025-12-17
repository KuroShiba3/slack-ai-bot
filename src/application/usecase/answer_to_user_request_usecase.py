from ...domain.model import Conversation
from ...domain.service import AgentWorkflowService
from ...domain.repository import ConversationRepository
from ..dto.answer_to_user_request_usecase import AnswerToUserRequestInput, AnswerToUserRequestOutput


class AnswerToUserRequestUseCase:
    def __init__(
        self,
        workflow_service: AgentWorkflowService,
        conversation_repository: ConversationRepository,
    ):
        self._workflow_service = workflow_service
        self._conversation_repository = conversation_repository

    async def execute(self, input_dto: AnswerToUserRequestInput) -> AnswerToUserRequestOutput:

        # 会話履歴の取得
        conversation = None
        conversation_id = input_dto.context.get("conversation_id", "")
        if conversation_id:
            conversation = await self._conversation_repository.find_by_id(conversation_id)
        if conversation is None:
            conversation = Conversation.create()

        # ユーザーメッセージの追加
        conversation.append_user_message(input_dto.user_message)

        # AIワークフロー実行
        final_answer = await self._workflow_service.execute(user_message=input_dto.user_message, context=input_dto.context)

        # AIの回答を会話履歴に追加して保存
        conversation.append_assistant_message(final_answer)
        await self._conversation_repository.save(conversation)

        return AnswerToUserRequestOutput(answer=final_answer)