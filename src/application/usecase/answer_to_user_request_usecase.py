from ...domain.model import ChatSession
from ...domain.repository import IChatSessionRepository
from ...domain.service.interfaces.workflow_service import IWorkflowService
from ..dto.answer_to_user_request_usecase import (
    AnswerToUserRequestInput,
    AnswerToUserRequestOutput,
)


class AnswerToUserRequestUseCase:
    def __init__(
        self,
        workflow_service: IWorkflowService,
        chat_session_repository: IChatSessionRepository,
    ):
        self._workflow_service = workflow_service
        self._chat_session_repository = chat_session_repository

    async def execute(
        self, input_dto: AnswerToUserRequestInput
    ) -> AnswerToUserRequestOutput:
        conversation_id = input_dto.context.get("conversation_id")
        if not conversation_id:
            raise ValueError("conversation_idがコンテキストに存在しません")

        # チャットセッションを取得または作成
        chat_session = await self._chat_session_repository.find_by_id(conversation_id)
        if not chat_session:
            chat_session = ChatSession.create(id=conversation_id)

        # ユーザーメッセージを追加
        chat_session.add_user_message(input_dto.user_message)

        # ワークフロー実行
        result = await self._workflow_service.execute(chat_session, input_dto.context)

        # 結果をチャットセッションに追加
        chat_session.add_assistant_message(result.answer)
        chat_session.add_task_plan(result.task_plan)

        # 保存
        await self._chat_session_repository.save(chat_session)

        # 回答を返す
        return AnswerToUserRequestOutput(
            answer=result.answer, message_id=chat_session.last_assistant_message_id() or ""
        )
