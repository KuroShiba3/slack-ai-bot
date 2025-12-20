from ...domain.model import Conversation
from ...domain.repository import ConversationRepository
from ...domain.service.agent_workflow_service import IAgentWorkflowService
from ..dto.answer_to_user_request_usecase import (
    AnswerToUserRequestInput,
    AnswerToUserRequestOutput,
)


class AnswerToUserRequestUseCase:
    def __init__(
        self,
        workflow_service: IAgentWorkflowService,
        conversation_repository: ConversationRepository,
    ):
        self._workflow_service = workflow_service
        self._conversation_repository = conversation_repository

    async def execute(self, input_dto: AnswerToUserRequestInput) -> AnswerToUserRequestOutput:
        thread_id = input_dto.context.get("thread_ts")

        # 会話を取得または作成
        conversation = await self._conversation_repository.find_by_thread_id(thread_id)
        if not conversation:
            conversation = Conversation.create()

        # ユーザーメッセージを追加
        conversation.add_user_message(input_dto.user_message)

        # ワークフロー実行
        result = await self._workflow_service.execute(conversation, input_dto.context)

        # 結果を会話に追加
        conversation.add_assistant_message(result.answer)
        conversation.add_task_plan(result.task_plan)

        # 保存
        await self._conversation_repository.save(conversation)

        # 回答を返す
        return AnswerToUserRequestOutput(answer=result.answer)
