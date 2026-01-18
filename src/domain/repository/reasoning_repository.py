from abc import ABC, abstractmethod
from typing import List

from src.domain.models.task import Task
from src.domain.models.note import Note
from src.domain.models.calendar import Event


class ReasoningRepository(ABC):
    @abstractmethod
    def generate_tasks(
        self, arhievment_rate: float, relevant_notes: List[Note], events: List[Event]
    ) -> List[Task]:
        """達成率と関連するノートからタスクを生成する
        Args:
            arhievment_rate(float): 達成率
            relevant_notes(List[Note]): 関連するノート
            events(List[Event]): イベント
        Returns:
            List[Task]: 生成されたタスク
        """
        pass
