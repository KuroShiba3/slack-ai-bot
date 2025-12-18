from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

from .task_log import TaskLog


class AgentName(Enum):
    WEB_SEARCH = "web_search"
    GENERAL_ANSWER = "general_answer"

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
        status: TaskStatus,
        result: str | None,
        task_log: TaskLog | None,
        created_at: datetime,
        completed_at: datetime | None,
    ):
        if not description:
            raise ValueError("タスクの説明が空です。")
        if not agent_name:
            raise ValueError("エージェント名が空です。")

        self._id = id
        self._description = description
        self._agent_name = agent_name
        self._status = status
        self._result = result
        self._task_log = task_log
        self._created_at = created_at
        self._completed_at = completed_at

    @classmethod
    def create(cls, description: str, agent_name: AgentName) -> "Task":
        created_at = datetime.now()
        completed_at = None
        return cls(
            id=uuid4(),
            description=description,
            agent_name=agent_name,
            status=TaskStatus.IN_PROGRESS,
            result=None,
            work_log=None,
            created_at=created_at,
            completed_at=completed_at,
        )

    @classmethod
    def reconstruct(
        cls,
        id: UUID,
        description: str,
        agent_name: AgentName,
        status: TaskStatus,
        result: str,
        task_log: TaskLog | None,
        created_at: datetime,
        completed_at: datetime | None,
    ) -> "Task":
        return cls(
            id=id,
            description=description,
            agent_name=agent_name,
            status=status,
            result=result,
            task_log=task_log,
            created_at=created_at,
            completed_at=completed_at,
        )

    @property
    def id(self) -> str:
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
    def task_log(self) -> TaskLog | None:
        return self._task_log

    def set_task_log(self, task_log: TaskLog) -> None:
        """作業ログを設定(エージェントが作業開始時に設定)"""
        if self._task_log is not None:
            raise ValueError("作業ログは既に設定されています")
        self._task_log = task_log
        self._task_log.mark_started()
        self._completed_at = None

    def complete(self, result: str) -> None:
        """タスクを完了し、結果を記録"""
        if self._status != TaskStatus.IN_PROGRESS:
            raise ValueError(f"実行中でないタスクは完了できません: {self._status}")
        if not result:
            raise ValueError("結果が空です。")

        self._status = TaskStatus.COMPLETED
        self._result = result
        if self._task_log:
            self._task_log.mark_completed()
        self._completed_at = datetime.now()

    def fail(self, error_message: str) -> None:
        """タスクを失敗として記録"""
        self._status = TaskStatus.FAILED
        self._result = f"Error: {error_message}"
        if self._task_log:
            self._task_log.mark_failed(error_message)
        self._completed_at = datetime.now()

    def should_retry(self) -> bool:
        """リトライすべきか判定"""
        if self._task_log:
            return self._task_log.should_retry()
        return False
