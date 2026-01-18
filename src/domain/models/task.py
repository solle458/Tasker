from dataclasses import dataclass, field
from enum import Enum, auto


class TaskType(Enum):
    """Task type enum
    Attributes:
        Daily: 日次タスク（毎日のルーティン）
        Must: 必須タスク
        Should: やるべきタスク
        Could: できればやるタスク
    """

    Daily = auto()
    Must = auto()
    Should = auto()
    Could = auto()


@dataclass
class Task:
    """Task entity
    Attributes:
        name(str): タスクの名前
        task_type(TaskType): タスクの種類
        is_completed(bool): 完了フラグ
    """

    name: str = field(default="")
    task_type: TaskType = field(default=TaskType.Daily)
    is_completed: bool = field(default=False)
