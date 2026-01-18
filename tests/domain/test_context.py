"""
domain/models/context.py のテスト
"""

import pytest
from datetime import datetime

from src.domain.models.context import InitialContext, NoteMetadata
from src.domain.models.note import Note, NoteType, Property
from src.domain.models.calendar import Event


# =============================================================================
# フィクスチャ
# =============================================================================


@pytest.fixture
def sample_note():
    """サンプルノート"""
    prop = Property(
        tags=["obsidian/section/literature", "project/test"],
        title="テストノート",
        aliases=["テスト"],
        uid="test-001",
    )
    return Note(
        name="test_note.md",
        properties=prop,
        content="# テストノート\n\nこれはテスト用のコンテンツです。",
        links=["Related-Note.md", "Another-Note.md"],
        note_type=NoteType.Literature,
    )


@pytest.fixture
def sample_index_note():
    """サンプルIndexノート"""
    prop = Property(
        tags=["obsidian/section/index"],
        title="長期目標",
        aliases=[],
        uid="index-001",
    )
    return Note(
        name="Index.md",
        properties=prop,
        content="# 長期目標\n\n- 目標1: プロジェクト完成\n- 目標2: スキルアップ",
        links=[],
        note_type=NoteType.Index,
    )


@pytest.fixture
def sample_daily_notes():
    """サンプルDailyノートリスト"""
    notes = []
    for i in range(3):
        prop = Property(
            tags=["obsidian/section/daily"],
            title=f"Daily 2026-01-{15 + i}",
            aliases=[],
            uid=f"daily-{i}",
        )
        note = Note(
            name=f"2026-01-{15 + i}.md",
            properties=prop,
            content=f"# 2026-01-{15 + i}\n\n今日のタスク:\n- タスク{i}",
            links=[],
            note_type=NoteType.Daily,
        )
        notes.append(note)
    return notes


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


# =============================================================================
# NoteMetadata テスト
# =============================================================================


class TestNoteMetadata:
    """NoteMetadata のテスト"""

    def test_default_values(self):
        """デフォルト値でインスタンス化できることを確認"""
        meta = NoteMetadata()

        assert meta.name == ""
        assert meta.title == ""
        assert meta.tags == []
        assert meta.note_type == NoteType.Literature
        assert meta.links == []

    def test_with_arguments(self):
        """引数を指定してインスタンス化できることを確認"""
        meta = NoteMetadata(
            name="test.md",
            title="テスト",
            tags=["tag1", "tag2"],
            note_type=NoteType.Index,
            links=["link1.md"],
        )

        assert meta.name == "test.md"
        assert meta.title == "テスト"
        assert meta.tags == ["tag1", "tag2"]
        assert meta.note_type == NoteType.Index
        assert meta.links == ["link1.md"]

    def test_from_note(self, sample_note):
        """Note から NoteMetadata を生成できることを確認"""
        meta = NoteMetadata.from_note(sample_note)

        assert meta.name == "test_note.md"
        assert meta.title == "テストノート"
        assert "obsidian/section/literature" in meta.tags
        assert "project/test" in meta.tags
        assert meta.note_type == NoteType.Literature
        assert "Related-Note.md" in meta.links

    def test_to_dict(self, sample_note):
        """辞書形式に変換できることを確認"""
        meta = NoteMetadata.from_note(sample_note)
        result = meta.to_dict()

        assert result["name"] == "test_note.md"
        assert result["title"] == "テストノート"
        assert result["note_type"] == "Literature"
        assert isinstance(result["tags"], list)
        assert isinstance(result["links"], list)


# =============================================================================
# InitialContext テスト
# =============================================================================


class TestInitialContext:
    """InitialContext のテスト"""

    def test_default_values(self):
        """デフォルト値でインスタンス化できることを確認"""
        ctx = InitialContext()

        assert ctx.index_notes == []
        assert ctx.weekly_daily_notes == []
        assert ctx.events == []
        assert ctx.achievement_rate == 0.0
        assert ctx.note_metadata_list == []

    def test_with_arguments(
        self, sample_index_note, sample_daily_notes, sample_events, sample_note
    ):
        """引数を指定してインスタンス化できることを確認"""
        metadata_list = [NoteMetadata.from_note(sample_note)]

        ctx = InitialContext(
            index_notes=[sample_index_note],
            weekly_daily_notes=sample_daily_notes,
            events=sample_events,
            achievement_rate=0.75,
            note_metadata_list=metadata_list,
        )

        assert len(ctx.index_notes) == 1
        assert len(ctx.weekly_daily_notes) == 3
        assert len(ctx.events) == 2
        assert ctx.achievement_rate == 0.75
        assert len(ctx.note_metadata_list) == 1

    def test_format_for_prompt_contains_achievement_rate(self):
        """フォーマットに達成率が含まれることを確認"""
        ctx = InitialContext(achievement_rate=0.8)
        result = ctx.format_for_prompt()

        assert "80.0%" in result

    def test_format_for_prompt_contains_index_notes(self, sample_index_note):
        """フォーマットにIndexノートが含まれることを確認"""
        ctx = InitialContext(index_notes=[sample_index_note])
        result = ctx.format_for_prompt()

        assert "Index ノート" in result
        assert "長期目標" in result

    def test_format_for_prompt_contains_daily_notes(self, sample_daily_notes):
        """フォーマットにDailyノートが含まれることを確認"""
        ctx = InitialContext(weekly_daily_notes=sample_daily_notes)
        result = ctx.format_for_prompt()

        assert "Daily ノート" in result

    def test_format_for_prompt_contains_events(self, sample_events):
        """フォーマットにイベントが含まれることを確認"""
        ctx = InitialContext(events=sample_events)
        result = ctx.format_for_prompt()

        assert "今日の予定" in result
        assert "朝会" in result
        assert "プロジェクト会議" in result

    def test_format_for_prompt_contains_metadata(self, sample_note):
        """フォーマットにメタデータが含まれることを確認"""
        metadata_list = [NoteMetadata.from_note(sample_note)]
        ctx = InitialContext(note_metadata_list=metadata_list)
        result = ctx.format_for_prompt()

        assert "ノート一覧" in result
        assert "test_note.md" in result

    def test_format_for_prompt_truncates_long_content(self, sample_index_note):
        """長いコンテンツが切り詰められることを確認"""
        # 長いコンテンツを持つDailyノートを作成
        prop = Property(tags=["obsidian/section/daily"], title="Long Daily")
        long_note = Note(
            name="long.md",
            properties=prop,
            content="# Long Content\n\n" + "x" * 1000,
            links=[],
            note_type=NoteType.Daily,
        )

        ctx = InitialContext(weekly_daily_notes=[long_note])
        result = ctx.format_for_prompt()

        # 500文字 + "..." で切り詰められていることを確認
        assert "..." in result

    def test_format_for_prompt_empty_context(self):
        """空のコンテキストでもフォーマットできることを確認"""
        ctx = InitialContext()
        result = ctx.format_for_prompt()

        # 達成率のセクションは常に存在
        assert "達成率" in result
        assert "0.0%" in result
