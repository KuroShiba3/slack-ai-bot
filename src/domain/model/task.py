from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

from src.domain.exception.task_exception import (
    EmptyTaskDescriptionError,
    MissingTaskLogError,
    TaskNotCompletedError,
    TaskNotInProgressError,
)

from .general_answer_task_log import GeneralAnswerTaskLog
from .task_log import TaskLog
from .web_search_task_log import SearchResult, WebSearchTaskLog


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
            raise EmptyTaskDescriptionError()
        if not task_log:
            raise MissingTaskLogError()

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
            created_at=datetime.now(),
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
            created_at=datetime.now(),
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

    def complete(self, result: str) -> None:
        """タスクを完了し、結果を記録"""
        if self._status != TaskStatus.IN_PROGRESS:
            raise TaskNotInProgressError(self._status.value)

        if not result or not result.strip():
            self.fail("タスク実行結果が空でした")
            return

        self._status = TaskStatus.COMPLETED
        self._result = result
        self._completed_at = datetime.now()

    def update_result(self, result: str) -> None:
        """タスクの結果を更新"""
        if self._status != TaskStatus.COMPLETED:
            raise TaskNotCompletedError(self._status.value)

        if not result or not result.strip():
            self.fail("タスク実行結果が空でした")
            return

        self._result = result
        self._completed_at = datetime.now()

    def fail(self, error_message: str) -> None:
        """タスクを失敗として記録"""
        self._status = TaskStatus.FAILED
        self._result = f"Error: {error_message}"
        self._completed_at = datetime.now()

    def add_web_search_attempt(self, query: str, results: list[SearchResult]) -> None:
        """Web検索の試行を記録"""
        if not isinstance(self._task_log, WebSearchTaskLog):
            raise TypeError(
                f"このタスクはWeb検索タスクではありません。AgentName: {self._agent_name}"
            )
        self._task_log.add_attempt(query=query, results=results)

    def add_general_answer_attempt(self, response: str) -> None:
        """一般回答の試行を記録"""
        if not isinstance(self._task_log, GeneralAnswerTaskLog):
            raise TypeError(
                f"このタスクは一般回答タスクではありません。AgentName: {self._agent_name}"
            )
        self._task_log.add_attempt(response=response)
