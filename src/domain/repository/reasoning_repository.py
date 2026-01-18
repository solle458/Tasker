from abc import ABC, abstractmethod
from typing import List

from src.domain.models.task import Task
from src.domain.models.context import InitialContext


class ReasoningRepository(ABC):
    @abstractmethod
    def generate_tasks(self, initial_context: InitialContext) -> List[Task]:
        """初期コンテキストからタスクを生成する

        Gemini が Function Calling を使って自律的にノートを探索し、
        今日のタスクを生成する。

        Args:
            initial_context(InitialContext): 初期コンテキスト
                - index_notes: 長期目標（Index ノート）
                - weekly_daily_notes: 過去7日分の Daily ノート
                - events: カレンダーのイベント一覧
                - achievement_rate: 昨日の達成率
                - note_metadata_list: 全ノートのメタデータ（目次）

        Returns:
            List[Task]: 生成されたタスク
        """
        pass
