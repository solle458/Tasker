"""
usecase/generate_daily_tasks.py のテスト
"""

import pytest
from unittest.mock import Mock
from datetime import datetime

from src.usecase.generate_daily_tasks import GenerateDailyTasksUseCase
from src.domain.models.task import Task, TaskType
from src.domain.models.note import Note, NoteType, Property
from src.domain.models.calendar import Event
from src.domain.models.context import InitialContext


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
def sample_index_notes():
    """サンプルIndexノートリスト"""
    prop = Property(
        tags=["obsidian/section/index"],
        title="Index Note",
        aliases=[],
        uid="index-001",
    )
    return [
        Note(
            name="Index.md",
            properties=prop,
            content="# 長期目標\n\n- 目標1\n- 目標2",
            links=[],
            note_type=NoteType.Index,
        )
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
def sample_all_notes(sample_index_notes, sample_weekly_notes):
    """全ノートリスト"""
    return sample_index_notes + sample_weekly_notes


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
        sample_index_notes,
        sample_weekly_notes,
        sample_all_notes,
        sample_generated_tasks,
    ):
        """execが全てのリポジトリメソッドを正しく呼び出すことを確認"""
        # モックの設定
        mock_calendar_repository.get_events.return_value = sample_events
        mock_note_repository.find_by_note_type.return_value = sample_index_notes
        mock_note_repository.get_daily_notes.return_value = sample_weekly_notes
        mock_note_repository.achievement_rate.return_value = 0.8
        mock_note_repository.get_all_notes.return_value = sample_all_notes
        mock_reasoning_repository.generate_tasks.return_value = sample_generated_tasks

        # 実行
        result = use_case.exec()

        # 検証
        mock_calendar_repository.get_events.assert_called_once()
        mock_note_repository.find_by_note_type.assert_called_once_with(NoteType.Index)
        mock_note_repository.get_daily_notes.assert_called_once_with(7, exclude_today=True)
        mock_note_repository.get_all_notes.assert_called_once()
        mock_reasoning_repository.generate_tasks.assert_called_once()

        # InitialContext が渡されていることを確認
        call_args = mock_reasoning_repository.generate_tasks.call_args
        initial_context = call_args[0][0]
        assert isinstance(initial_context, InitialContext)
        assert initial_context.achievement_rate == 0.8
        assert len(initial_context.index_notes) == 1
        assert len(initial_context.weekly_daily_notes) == 7

        assert result == sample_generated_tasks

    def test_exec_returns_tasks(
        self,
        use_case,
        mock_calendar_repository,
        mock_note_repository,
        mock_reasoning_repository,
        sample_events,
        sample_index_notes,
        sample_weekly_notes,
        sample_all_notes,
        sample_generated_tasks,
    ):
        """execがタスクリストを返すことを確認"""
        # モックの設定
        mock_calendar_repository.get_events.return_value = sample_events
        mock_note_repository.find_by_note_type.return_value = sample_index_notes
        mock_note_repository.get_daily_notes.return_value = sample_weekly_notes
        mock_note_repository.achievement_rate.return_value = 0.75
        mock_note_repository.get_all_notes.return_value = sample_all_notes
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
        sample_index_notes,
        sample_weekly_notes,
        sample_all_notes,
    ):
        """イベントが空の場合の動作を確認"""
        # モックの設定
        mock_calendar_repository.get_events.return_value = []
        mock_note_repository.find_by_note_type.return_value = sample_index_notes
        mock_note_repository.get_daily_notes.return_value = sample_weekly_notes
        mock_note_repository.achievement_rate.return_value = 0.5
        mock_note_repository.get_all_notes.return_value = sample_all_notes
        mock_reasoning_repository.generate_tasks.return_value = []

        # 実行
        result = use_case.exec()

        # InitialContext に空のイベントが渡されていることを確認
        call_args = mock_reasoning_repository.generate_tasks.call_args
        initial_context = call_args[0][0]
        assert initial_context.events == []

        assert result == []

    def test_exec_with_no_daily_notes(
        self,
        use_case,
        mock_calendar_repository,
        mock_note_repository,
        mock_reasoning_repository,
        sample_events,
        sample_index_notes,
    ):
        """Dailyノートがない場合の動作を確認"""
        # モックの設定
        mock_calendar_repository.get_events.return_value = sample_events
        mock_note_repository.find_by_note_type.return_value = sample_index_notes
        mock_note_repository.get_daily_notes.return_value = []
        mock_note_repository.get_all_notes.return_value = sample_index_notes
        mock_reasoning_repository.generate_tasks.return_value = []

        # 実行
        use_case.exec()

        # Dailyノートがない場合、achievement_rate は呼ばれない
        mock_note_repository.achievement_rate.assert_not_called()

        # InitialContext に achievement_rate = 0.0 が渡されていることを確認
        call_args = mock_reasoning_repository.generate_tasks.call_args
        initial_context = call_args[0][0]
        assert initial_context.achievement_rate == 0.0

    def test_exec_with_low_achievement_rate(
        self,
        use_case,
        mock_calendar_repository,
        mock_note_repository,
        mock_reasoning_repository,
        sample_events,
        sample_index_notes,
        sample_weekly_notes,
        sample_all_notes,
        sample_generated_tasks,
    ):
        """達成率が低い場合の動作を確認"""
        # モックの設定
        mock_calendar_repository.get_events.return_value = sample_events
        mock_note_repository.find_by_note_type.return_value = sample_index_notes
        mock_note_repository.get_daily_notes.return_value = sample_weekly_notes
        mock_note_repository.achievement_rate.return_value = 0.2
        mock_note_repository.get_all_notes.return_value = sample_all_notes
        mock_reasoning_repository.generate_tasks.return_value = sample_generated_tasks

        # 実行
        result = use_case.exec()

        # InitialContext に achievement_rate = 0.2 が渡されていることを確認
        call_args = mock_reasoning_repository.generate_tasks.call_args
        initial_context = call_args[0][0]
        assert initial_context.achievement_rate == 0.2

        assert result == sample_generated_tasks

    def test_exec_with_no_index_notes(
        self,
        use_case,
        mock_calendar_repository,
        mock_note_repository,
        mock_reasoning_repository,
        sample_events,
        sample_weekly_notes,
    ):
        """Indexノートがない場合の動作を確認"""
        # モックの設定
        mock_calendar_repository.get_events.return_value = sample_events
        mock_note_repository.find_by_note_type.return_value = []
        mock_note_repository.get_daily_notes.return_value = sample_weekly_notes
        mock_note_repository.achievement_rate.return_value = 0.6
        mock_note_repository.get_all_notes.return_value = sample_weekly_notes
        mock_reasoning_repository.generate_tasks.return_value = [
            Task(name="基本タスク", task_type=TaskType.Daily, is_completed=False)
        ]

        # 実行
        result = use_case.exec()

        # InitialContext に空の index_notes が渡されていることを確認
        call_args = mock_reasoning_repository.generate_tasks.call_args
        initial_context = call_args[0][0]
        assert initial_context.index_notes == []

        assert len(result) == 1

    def test_exec_builds_note_metadata_list(
        self,
        use_case,
        mock_calendar_repository,
        mock_note_repository,
        mock_reasoning_repository,
        sample_events,
        sample_index_notes,
        sample_weekly_notes,
        sample_all_notes,
        sample_generated_tasks,
    ):
        """ノートメタデータリストが正しく構築されることを確認"""
        # モックの設定
        mock_calendar_repository.get_events.return_value = sample_events
        mock_note_repository.find_by_note_type.return_value = sample_index_notes
        mock_note_repository.get_daily_notes.return_value = sample_weekly_notes
        mock_note_repository.achievement_rate.return_value = 0.7
        mock_note_repository.get_all_notes.return_value = sample_all_notes
        mock_reasoning_repository.generate_tasks.return_value = sample_generated_tasks

        # 実行
        use_case.exec()

        # InitialContext の note_metadata_list が全ノート数と一致することを確認
        call_args = mock_reasoning_repository.generate_tasks.call_args
        initial_context = call_args[0][0]
        assert len(initial_context.note_metadata_list) == len(sample_all_notes)
