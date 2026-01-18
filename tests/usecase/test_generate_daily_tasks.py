"""
usecase/generate_daily_tasks.py のテスト
"""

import pytest
from unittest.mock import Mock

from src.usecase.generate_daily_tasks import GenerateDailyTasksUseCase
from src.domain.models.task import Task, TaskType
from src.domain.models.note import Note, NoteType, Property
from src.domain.models.calendar import Event


# =============================================================================
# フィクスチャ
# =============================================================================


@pytest.fixture
def mock_calendar_repository():
    """モックカレンダーリポジトリ"""
    return Mock()


@pytest.fixture
def mock_note_repository():
    """モックノートリポジトリ"""
    return Mock()


@pytest.fixture
def mock_reasoning_repository():
    """モック思考リポジトリ"""
    return Mock()


@pytest.fixture
def use_case(mock_calendar_repository, mock_note_repository, mock_reasoning_repository):
    """テスト用のGenerateDailyTasksUseCaseインスタンス"""
    return GenerateDailyTasksUseCase(
        calendar_repository=mock_calendar_repository,
        note_repository=mock_note_repository,
        reasoning_repository=mock_reasoning_repository,
    )


@pytest.fixture
def sample_events():
    """サンプルイベントリスト"""
    from datetime import datetime

    return [
        Event(
            name="朝会",
            start=datetime(2026, 1, 18, 9, 0),
            end=datetime(2026, 1, 18, 9, 30),
            description="毎日の朝会",
        ),
        Event(
            name="プロジェクト会議",
            start=datetime(2026, 1, 18, 14, 0),
            end=datetime(2026, 1, 18, 15, 0),
            description="週次レビュー",
        ),
    ]


@pytest.fixture
def sample_weekly_notes():
    """サンプル週間ノートリスト"""
    notes = []
    for i in range(7):
        prop = Property(
            tags=["obsidian/section/daily"],
            title=f"Daily Note 2026-01-{11 + i}",
            aliases=[],
            uid=f"daily-2026-01-{11 + i}",
        )
        note = Note(
            name=f"2026-01-{11 + i}.md",
            properties=prop,
            content=f"# 2026-01-{11 + i}\n\n## Tasks\n- タスク{i}",
            links=[],
            note_type=NoteType.Daily,
        )
        notes.append(note)
    return notes


@pytest.fixture
def sample_relevant_notes():
    """サンプル関連ノートリスト"""
    prop = Property(
        tags=["obsidian/section/literature"],
        title="プロジェクト関連ノート",
        aliases=[],
        uid="project-001",
    )
    return [
        Note(
            name="project_note.md",
            properties=prop,
            content="# プロジェクト\n\n関連情報",
            links=[],
            note_type=NoteType.Literature,
        )
    ]


@pytest.fixture
def sample_generated_tasks():
    """サンプル生成タスクリスト"""
    return [
        Task(name="朝会に参加", task_type=TaskType.Daily, is_completed=False),
        Task(name="プロジェクト資料準備", task_type=TaskType.Must, is_completed=False),
        Task(name="メール確認", task_type=TaskType.Should, is_completed=False),
    ]


# =============================================================================
# 初期化テスト
# =============================================================================


class TestGenerateDailyTasksUseCaseInit:
    """GenerateDailyTasksUseCase 初期化のテスト"""

    def test_init_with_repositories(
        self, mock_calendar_repository, mock_note_repository, mock_reasoning_repository
    ):
        """リポジトリを指定して初期化"""
        use_case = GenerateDailyTasksUseCase(
            calendar_repository=mock_calendar_repository,
            note_repository=mock_note_repository,
            reasoning_repository=mock_reasoning_repository,
        )

        assert use_case.calendar_repository == mock_calendar_repository
        assert use_case.note_repository == mock_note_repository
        assert use_case.reasoning_repository == mock_reasoning_repository


# =============================================================================
# exec メソッドテスト
# =============================================================================


class TestExec:
    """exec メソッドのテスト"""

    def test_exec_calls_all_repositories(
        self,
        use_case,
        mock_calendar_repository,
        mock_note_repository,
        mock_reasoning_repository,
        sample_events,
        sample_weekly_notes,
        sample_relevant_notes,
        sample_generated_tasks,
    ):
        """execが全てのリポジトリメソッドを正しく呼び出すことを確認"""
        # モックの設定
        mock_calendar_repository.get_events.return_value = sample_events
        mock_note_repository.get_daily_notes.return_value = sample_weekly_notes
        mock_note_repository.arhievment_rate.return_value = 0.8
        mock_note_repository.find_relevant_notes.return_value = sample_relevant_notes
        mock_reasoning_repository.generate_tasks.return_value = sample_generated_tasks

        # 実行
        result = use_case.exec()

        # 検証
        mock_calendar_repository.get_events.assert_called_once()
        mock_note_repository.get_daily_notes.assert_called_once_with(7)
        mock_note_repository.arhievment_rate.assert_called_once_with(
            sample_weekly_notes[0]
        )
        mock_note_repository.find_relevant_notes.assert_called_once_with(
            events=sample_events, weekly_notes=sample_weekly_notes
        )
        mock_reasoning_repository.generate_tasks.assert_called_once_with(
            arhievment_rate=0.8,
            relevant_notes=sample_relevant_notes,
            events=sample_events,
        )
        assert result == sample_generated_tasks

    def test_exec_returns_tasks(
        self,
        use_case,
        mock_calendar_repository,
        mock_note_repository,
        mock_reasoning_repository,
        sample_events,
        sample_weekly_notes,
        sample_relevant_notes,
        sample_generated_tasks,
    ):
        """execがタスクリストを返すことを確認"""
        # モックの設定
        mock_calendar_repository.get_events.return_value = sample_events
        mock_note_repository.get_daily_notes.return_value = sample_weekly_notes
        mock_note_repository.arhievment_rate.return_value = 0.75
        mock_note_repository.find_relevant_notes.return_value = sample_relevant_notes
        mock_reasoning_repository.generate_tasks.return_value = sample_generated_tasks

        # 実行
        result = use_case.exec()

        # 検証
        assert isinstance(result, list)
        assert len(result) == 3
        assert all(isinstance(task, Task) for task in result)

    def test_exec_with_empty_events(
        self,
        use_case,
        mock_calendar_repository,
        mock_note_repository,
        mock_reasoning_repository,
        sample_weekly_notes,
        sample_relevant_notes,
    ):
        """イベントが空の場合の動作を確認"""
        # モックの設定
        mock_calendar_repository.get_events.return_value = []
        mock_note_repository.get_daily_notes.return_value = sample_weekly_notes
        mock_note_repository.arhievment_rate.return_value = 0.5
        mock_note_repository.find_relevant_notes.return_value = sample_relevant_notes
        mock_reasoning_repository.generate_tasks.return_value = []

        # 実行
        result = use_case.exec()

        # 検証
        mock_note_repository.find_relevant_notes.assert_called_once_with(
            events=[], weekly_notes=sample_weekly_notes
        )
        mock_reasoning_repository.generate_tasks.assert_called_once_with(
            arhievment_rate=0.5,
            relevant_notes=sample_relevant_notes,
            events=[],
        )
        assert result == []

    def test_exec_with_low_achievement_rate(
        self,
        use_case,
        mock_calendar_repository,
        mock_note_repository,
        mock_reasoning_repository,
        sample_events,
        sample_weekly_notes,
        sample_relevant_notes,
        sample_generated_tasks,
    ):
        """達成率が低い場合の動作を確認"""
        # モックの設定
        mock_calendar_repository.get_events.return_value = sample_events
        mock_note_repository.get_daily_notes.return_value = sample_weekly_notes
        mock_note_repository.arhievment_rate.return_value = 0.2
        mock_note_repository.find_relevant_notes.return_value = sample_relevant_notes
        mock_reasoning_repository.generate_tasks.return_value = sample_generated_tasks

        # 実行
        result = use_case.exec()

        # 検証
        mock_reasoning_repository.generate_tasks.assert_called_once_with(
            arhievment_rate=0.2,
            relevant_notes=sample_relevant_notes,
            events=sample_events,
        )
        assert result == sample_generated_tasks

    def test_exec_with_no_relevant_notes(
        self,
        use_case,
        mock_calendar_repository,
        mock_note_repository,
        mock_reasoning_repository,
        sample_events,
        sample_weekly_notes,
    ):
        """関連ノートがない場合の動作を確認"""
        # モックの設定
        mock_calendar_repository.get_events.return_value = sample_events
        mock_note_repository.get_daily_notes.return_value = sample_weekly_notes
        mock_note_repository.arhievment_rate.return_value = 0.6
        mock_note_repository.find_relevant_notes.return_value = []
        mock_reasoning_repository.generate_tasks.return_value = [
            Task(name="基本タスク", task_type=TaskType.Daily, is_completed=False)
        ]

        # 実行
        result = use_case.exec()

        # 検証
        mock_reasoning_repository.generate_tasks.assert_called_once_with(
            arhievment_rate=0.6,
            relevant_notes=[],
            events=sample_events,
        )
        assert len(result) == 1
