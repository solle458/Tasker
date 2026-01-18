from typing import List
from datetime import datetime, timezone, timedelta

from src.domain.repository.calendar_repository import CalendarRepository
from src.domain.repository.note_repository import NoteRepository
from src.domain.repository.reasoning_repository import ReasoningRepository
from src.domain.models.task import Task
from src.domain.models.note import NoteType
from src.domain.models.context import InitialContext, NoteMetadata


class GenerateDailyTasksUseCase:
    """Generate daily tasks use case

    Attributes:
        calendar_repository(CalendarRepository): カレンダーリポジトリ
        note_repository(NoteRepository): ノートリポジトリ
        reasoning_repository(ReasoningRepository): 思考リポジトリ
    """

    def __init__(
        self,
        calendar_repository: CalendarRepository,
        note_repository: NoteRepository,
        reasoning_repository: ReasoningRepository,
    ) -> None:
        self.calendar_repository = calendar_repository
        self.note_repository = note_repository
        self.reasoning_repository = reasoning_repository

    def exec(self) -> List[Task]:
        """実行する

        Returns:
            List[Task]: 生成されたタスク
        """
        # カレンダーイベントを取得（今日から30日分）
        events = self.calendar_repository.get_events(
            start_date=datetime.now(timezone.utc),
            end_date=datetime.now(timezone.utc) + timedelta(days=30),
            limit=100,
        )

        # Index ノートを取得（長期目標）
        index_notes = self.note_repository.find_by_note_type(NoteType.Index)

        # 過去7日間の Daily ノートを取得（当日のノートを除外）
        weekly_daily_notes = self.note_repository.get_daily_notes(7, exclude_today=True)

        # 達成率を計算（Daily ノートがある場合）
        achievement_rate = 0.0
        if weekly_daily_notes:
            yesterday_note = weekly_daily_notes[-1]  # 最新のノート
            achievement_rate = self.note_repository.achievement_rate(yesterday_note)

        # 全ノートのメタデータを取得（目次用）
        all_notes = self.note_repository.get_all_notes()
        note_metadata_list = [NoteMetadata.from_note(note) for note in all_notes]

        # InitialContext を構築
        initial_context = InitialContext(
            index_notes=index_notes,
            weekly_daily_notes=weekly_daily_notes,
            events=events,
            achievement_rate=achievement_rate,
            note_metadata_list=note_metadata_list,
        )

        # タスクを生成
        tasks = self.reasoning_repository.generate_tasks(initial_context)

        return tasks
