from typing import List
from datetime import datetime, timezone, timedelta

from src.domain.repository.calendar_repository import CalendarRepository
from src.domain.repository.note_repository import NoteRepository
from src.domain.repository.reasoning_repository import ReasoningRepository
from src.domain.models.task import Task


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
        events = self.calendar_repository.get_events(
            start_date=datetime.now(timezone.utc),
            end_date=datetime.now(timezone.utc) + timedelta(days=30),
            limit=100,
        )
        weekly_notes = self.note_repository.get_daily_notes(7)
        yesterday_note = weekly_notes[0]
        arhievment_rate = self.note_repository.arhievment_rate(yesterday_note)
        relevant_notes = self.note_repository.find_relevant_notes(
            events=events, weekly_notes=weekly_notes
        )
        tasks = self.reasoning_repository.generate_tasks(
            arhievment_rate=arhievment_rate,
            relevant_notes=relevant_notes,
            events=events,
        )
        return tasks
