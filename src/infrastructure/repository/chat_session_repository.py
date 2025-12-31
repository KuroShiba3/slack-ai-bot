import json
from datetime import datetime

from src.infrastructure.exception.repository_exception import (
    RepositoryFetchError,
    RepositorySaveError,
)

from ...domain.model.chat_session import ChatSession
from ...domain.model.general_answer_task_log import GeneralAnswerTaskLog
from ...domain.model.message import Message, Role
from ...domain.model.task import AgentName, Task, TaskStatus
from ...domain.model.task_plan import TaskPlan
from ...domain.model.web_search_task_log import WebSearchTaskLog
from ..database import DatabasePool


class ChatSessionRepository:
    async def save(self, chat_session: ChatSession) -> None:
        """チャットセッションと関連するメッセージを保存"""
        try:
            async with DatabasePool.get_connection() as conn:
                async with conn.transaction():
                    # チャットセッションを保存/更新
                    await conn.execute(
                        """
                        INSERT INTO chat_sessions (id, thread_id, user_id, channel_id, created_at, updated_at)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        ON CONFLICT (id) DO UPDATE SET
                            updated_at = EXCLUDED.updated_at
                        """,
                        (
                            chat_session.id,
                            chat_session.thread_id,
                            chat_session.user_id,
                            chat_session.channel_id,
                            chat_session.created_at,
                            datetime.now(),
                        ),
                    )

                    # メッセージを保存
                    messages_to_save = [
                        (
                            message.id,
                            chat_session.id,
                            message.role.value,
                            message.content,
                            message.created_at,
                        )
                        for message in chat_session.messages
                        if message.role != Role.SYSTEM
                    ]
                    if messages_to_save:
                        async with conn.cursor() as cur:
                            await cur.executemany(
                                """
                                INSERT INTO messages (id, chat_session_id, role, content, created_at)
                                VALUES (%s, %s, %s, %s, %s)
                                ON CONFLICT (id) DO UPDATE SET
                                    role = EXCLUDED.role,
                                    content = EXCLUDED.content
                                """,
                                messages_to_save,
                            )

                    # タスクプランとタスクを保存
                    for task_plan in chat_session.task_plans:
                        # タスクプランを保存
                        await conn.execute(
                            """
                            INSERT INTO task_plans (id, chat_session_id, message_id, created_at)
                            VALUES (%s, %s, %s, %s)
                            ON CONFLICT (id) DO NOTHING
                            """,
                            (
                                task_plan.id,
                                chat_session.id,
                                task_plan.message_id,
                                datetime.now(),
                            ),
                        )

                        # タスクを保存
                        for task in task_plan.tasks:
                            task_log_json = None
                            if task.task_log:
                                if hasattr(task.task_log, "to_dict"):
                                    task_log_json = json.dumps(task.task_log.to_dict())

                            await conn.execute(
                                """
                                INSERT INTO tasks (
                                    id, task_plan_id, description, agent_name,
                                    status, result, task_log_json,
                                    created_at, completed_at
                                )
                                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                                ON CONFLICT (id) DO UPDATE SET
                                    status = EXCLUDED.status,
                                    result = EXCLUDED.result,
                                    task_log_json = EXCLUDED.task_log_json,
                                    completed_at = EXCLUDED.completed_at
                                """,
                                (
                                    task.id,
                                    task_plan.id,
                                    task.description,
                                    task.agent_name.value,
                                    task.status.value,
                                    task.result,
                                    task_log_json,
                                    task.created_at,
                                    task.completed_at,
                                ),
                            )
        except Exception as e:
            raise RepositorySaveError("ChatSession", e) from e

    async def find_by_id(self, chat_session_id: str) -> ChatSession | None:
        """IDでチャットセッションを取得"""
        try:
            async with DatabasePool.get_connection() as conn:
                async with conn.cursor() as cur:
                    await cur.execute(
                        """
                        SELECT id, thread_id, user_id, channel_id, created_at, updated_at
                        FROM chat_sessions
                        WHERE id = %s
                        """,
                        (chat_session_id,),
                    )
                    session_row = await cur.fetchone()

                    if not session_row:
                        return None

                    await cur.execute(
                        """
                        SELECT id, role, content, created_at
                        FROM messages
                        WHERE chat_session_id = %s
                        ORDER BY created_at ASC
                        """,
                        (chat_session_id,),
                    )
                    message_rows = await cur.fetchall()

                messages = []
                for row in message_rows:
                    if row["role"] == "user":
                        role = Role.USER
                    elif row["role"] == "assistant":
                        role = Role.ASSISTANT
                    else:
                        continue  # システムメッセージは無視

                    message = Message.reconstruct(
                        id=row["id"],
                        role=role,
                        content=row["content"],
                        created_at=row["created_at"],
                    )
                    messages.append(message)

                # task_plansとtasksをJOINで一度に取得
                async with conn.cursor() as cur:
                    await cur.execute(
                        """
                        SELECT
                            tp.id as task_plan_id,
                            tp.message_id,
                            tp.created_at as task_plan_created_at,
                            t.id as task_id,
                            t.description,
                            t.agent_name,
                            t.status,
                            t.result,
                            t.task_log_json,
                            t.created_at as task_created_at,
                            t.completed_at
                        FROM task_plans tp
                        LEFT JOIN tasks t ON tp.id = t.task_plan_id
                        WHERE tp.chat_session_id = %s
                        ORDER BY tp.created_at ASC, t.created_at ASC
                        """,
                        (chat_session_id,),
                    )
                    rows = await cur.fetchall()

                # task_plan_idごとにグループ化してTaskPlanを構築
                from collections import defaultdict

                task_plans_dict = defaultdict(lambda: {"tasks": [], "info": None})

                for row in rows:
                    plan_id = row["task_plan_id"]

                    # TaskPlan情報を保存（初回のみ）
                    if task_plans_dict[plan_id]["info"] is None:
                        task_plans_dict[plan_id]["info"] = {
                            "id": plan_id,
                            "message_id": row["message_id"],
                            "created_at": row["task_plan_created_at"],
                        }

                    # Taskを追加（task_idがNoneでない場合のみ）
                    if row["task_id"] is not None:
                        agent_name = AgentName(row["agent_name"])

                        log_data = row["task_log_json"]
                        if isinstance(log_data, str):
                            log_data = json.loads(log_data)

                        task_log: WebSearchTaskLog | GeneralAnswerTaskLog
                        if agent_name == AgentName.WEB_SEARCH:
                            task_log = WebSearchTaskLog.from_dict(log_data)
                        elif agent_name == AgentName.GENERAL_ANSWER:
                            task_log = GeneralAnswerTaskLog.from_dict(log_data)
                        else:
                            raise ValueError(f"未知のagent_name: {agent_name}")

                        task = Task.reconstruct(
                            id=row["task_id"],
                            description=row["description"],
                            agent_name=agent_name,
                            task_log=task_log,
                            status=TaskStatus(row["status"]),
                            result=row["result"],
                            created_at=row["task_created_at"],
                            completed_at=row["completed_at"],
                        )
                        task_plans_dict[plan_id]["tasks"].append(task)

                # TaskPlanオブジェクトを構築
                task_plans = []
                for plan_data in task_plans_dict.values():
                    task_plan = TaskPlan(
                        id=plan_data["info"]["id"],
                        message_id=plan_data["info"]["message_id"],
                        tasks=plan_data["tasks"],
                    )
                    task_plans.append(task_plan)

                return ChatSession.reconstruct(
                    id=session_row["id"],
                    thread_id=session_row["thread_id"],
                    user_id=session_row["user_id"],
                    channel_id=session_row["channel_id"],
                    messages=messages,
                    task_plans=task_plans,
                    created_at=session_row["created_at"],
                    updated_at=session_row["updated_at"],
                )
        except Exception as e:
            raise RepositoryFetchError("ChatSession", e) from e
