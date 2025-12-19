from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

from .task_log import TaskLog
from .web_search_task_log import WebSearchTaskLog
from .general_answer_task_log import GeneralAnswerTaskLog


class AgentName(Enum):
    GENERAL_ANSWER = "general_answer"
    WEB_SEARCH = "web_search"

class TaskStatus(Enum):
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"

class Task:
    def __init__(
        self,
        id: UUID,
        description: str,
        agent_name: AgentName,
        task_log: TaskLog,
        status: TaskStatus = TaskStatus.IN_PROGRESS,
        result: str | None = None,
        created_at: datetime | None = None,
        completed_at: datetime | None = None,
    ):
        if not description:
            raise ValueError("タスクの説明が空です。")
        if not agent_name:
            raise ValueError("エージェント名が空です。")
        if not task_log:
            raise ValueError("タスクログが必要です。")

        self._id = id
        self._description = description
        self._agent_name = agent_name
        self._task_log = task_log
        self._status = status
        self._result = result
        self._created_at = created_at or datetime.now()
        self._completed_at = completed_at

    @classmethod
    def create_web_search(cls, description: str) -> "Task":
        """Web検索タスクを生成"""
        return cls(
            id=uuid4(),
            description=description,
            agent_name=AgentName.WEB_SEARCH,
            task_log=WebSearchTaskLog.create(),
            status=TaskStatus.IN_PROGRESS,
            created_at=datetime.now()
        )

    @classmethod
    def create_general_answer(cls, description: str) -> "Task":
        """一般回答タスクを生成"""
        return cls(
            id=uuid4(),
            description=description,
            agent_name=AgentName.GENERAL_ANSWER,
            task_log=GeneralAnswerTaskLog.create(),
            status=TaskStatus.IN_PROGRESS,
            created_at=datetime.now()
        )

    @classmethod
    def reconstruct(
        cls,
        id: UUID,
        description: str,
        agent_name: AgentName,
        task_log: TaskLog,
        status: TaskStatus,
        result: str | None,
        created_at: datetime,
        completed_at: datetime | None,
    ) -> "Task":
        """既存のタスクを再構築"""
        return cls(
            id=id,
            description=description,
            agent_name=agent_name,
            task_log=task_log,
            status=status,
            result=result,
            created_at=created_at,
            completed_at=completed_at,
        )

    @property
    def id(self) -> UUID:
        return self._id

    @property
    def description(self) -> str:
        return self._description

    @property
    def agent_name(self) -> AgentName:
        return self._agent_name

    @property
    def status(self) -> TaskStatus:
        return self._status

    @property
    def result(self) -> str | None:
        return self._result

    @property
    def created_at(self) -> datetime:
        return self._created_at

    @property
    def completed_at(self) -> datetime | None:
        return self._completed_at

    @property
    def task_log(self) -> TaskLog:
        return self._task_log

    def get_web_search_log(self) -> WebSearchTaskLog | None:
        """Web検索ログを取得（型安全）"""
        if isinstance(self._task_log, WebSearchTaskLog):
            return self._task_log
        return None

    def get_general_answer_log(self) -> GeneralAnswerTaskLog | None:
        """一般回答ログを取得（型安全）"""
        if isinstance(self._task_log, GeneralAnswerTaskLog):
            return self._task_log
        return None


    def complete(self, result: str) -> None:
        """タスクを完了し、結果を記録"""
        if self._status != TaskStatus.IN_PROGRESS:
            raise ValueError(f"実行中でないタスクは完了できません: {self._status}")
        if not result:
            raise ValueError("結果が空です。")

        self._status = TaskStatus.COMPLETED
        self._result = result
        self._completed_at = datetime.now()

    def fail(self, error_message: str) -> None:
        """タスクを失敗として記録"""
        self._status = TaskStatus.FAILED
        self._result = f"Error: {error_message}"
        self._completed_at = datetime.now()

    def to_dict(self) -> dict:
        """State保存用の辞書に変換"""
        return {
            "id": str(self._id),
            "description": self._description,
            "agent_name": self._agent_name.value,
            "status": self._status.value,
            "result": self._result,
            "task_log": self._task_log.to_dict() if self._task_log else {"type": "unknown", "attempts": []},
            "created_at": self._created_at.isoformat(),
            "completed_at": self._completed_at.isoformat() if self._completed_at else None
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Task":
        """辞書からTaskを復元"""
        from .web_search_task_log import WebSearchTaskLog
        from .general_answer_task_log import GeneralAnswerTaskLog

        # TaskLogの復元
        task_log_data = data.get("task_log", {})
        if task_log_data.get("type") == "web_search":
            task_log = WebSearchTaskLog.from_dict(task_log_data)
        elif task_log_data.get("type") == "general_answer":
            task_log = GeneralAnswerTaskLog.from_dict(task_log_data)
        else:
            # デフォルトでWebSearchTaskLogを作成
            task_log = WebSearchTaskLog()

        return cls.reconstruct(
            id=UUID(data["id"]),
            description=data["description"],
            agent_name=AgentName(data["agent_name"]),
            task_log=task_log,
            status=TaskStatus(data["status"]),
            result=data.get("result"),
            created_at=datetime.fromisoformat(data["created_at"]),
            completed_at=datetime.fromisoformat(data["completed_at"]) if data.get("completed_at") else None
        )
