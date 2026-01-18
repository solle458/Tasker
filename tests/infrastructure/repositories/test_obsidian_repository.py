"""
infrastructure/repositories/obsidian_repository.py のテスト
"""

import pytest

from src.infrastructure.repositories.obsidian_repository import ObsidianRepository
from src.domain.models.note import NoteType
from src.domain.exceptions import (
    NoteNotFoundError,
    InvalidVaultPathError,
)


# =============================================================================
# 単体テスト（ロジックのみ）
# =============================================================================


class TestExtractLinks:
    """_extract_links メソッドのテスト"""

    def test_basic_wiki_link(self, obsidian_repo):
        """基本的なWikiリンクを抽出"""
        content = "See [[Note1]] for more info."
        links = obsidian_repo._extract_links(content)
        assert links == ["Note1"]

    def test_multiple_wiki_links(self, obsidian_repo):
        """複数のWikiリンクを抽出"""
        content = "See [[Note1]] and [[Note2]] and [[Note3]]"
        links = obsidian_repo._extract_links(content)
        assert set(links) == {"Note1", "Note2", "Note3"}

    def test_wiki_link_with_alias(self, obsidian_repo):
        """エイリアス付きWikiリンクを抽出"""
        content = "See [[Note1|alias text]] for more info."
        links = obsidian_repo._extract_links(content)
        assert links == ["Note1"]

    def test_mixed_links(self, obsidian_repo):
        """通常リンクとエイリアス付きリンクの混在"""
        content = "See [[Note1]] and [[Note2|alias]]"
        links = obsidian_repo._extract_links(content)
        assert set(links) == {"Note1", "Note2"}

    def test_duplicate_links_removed(self, obsidian_repo):
        """重複するリンクは除去される"""
        content = "See [[Note1]] and [[Note1]] again"
        links = obsidian_repo._extract_links(content)
        assert links == ["Note1"]

    def test_no_links(self, obsidian_repo):
        """リンクがない場合は空リスト"""
        content = "No links here, just plain text."
        links = obsidian_repo._extract_links(content)
        assert links == []

    def test_empty_content(self, obsidian_repo):
        """空のコンテンツ"""
        links = obsidian_repo._extract_links("")
        assert links == []

    def test_link_with_spaces(self, obsidian_repo):
        """スペースを含むリンク"""
        content = "See [[Note With Spaces]]"
        links = obsidian_repo._extract_links(content)
        assert links == ["Note With Spaces"]


class TestDetermineNoteType:
    """_determine_note_type メソッドのテスト"""

    def test_index_type(self, obsidian_repo):
        """Indexタイプの判定"""
        tags = ["obsidian/section/index", "other"]
        assert obsidian_repo._determine_note_type(tags) == NoteType.Index

    def test_structure_type(self, obsidian_repo):
        """Structureタイプの判定"""
        tags = ["obsidian/section/structure"]
        assert obsidian_repo._determine_note_type(tags) == NoteType.Structure

    def test_daily_type(self, obsidian_repo):
        """Dailyタイプの判定"""
        tags = ["obsidian/section/daily"]
        assert obsidian_repo._determine_note_type(tags) == NoteType.Daily

    def test_literature_type(self, obsidian_repo):
        """Literatureタイプの判定"""
        tags = ["obsidian/section/literature"]
        assert obsidian_repo._determine_note_type(tags) == NoteType.Literature

    def test_fleeting_type(self, obsidian_repo):
        """Fleetingタイプの判定"""
        tags = ["obsidian/section/fleeting"]
        assert obsidian_repo._determine_note_type(tags) == NoteType.Fleeting

    def test_permanent_type(self, obsidian_repo):
        """Permanentタイプの判定"""
        tags = ["obsidian/section/permanent"]
        assert obsidian_repo._determine_note_type(tags) == NoteType.Permanent

    def test_default_type(self, obsidian_repo):
        """タグがない場合はLiteratureがデフォルト"""
        tags = ["random", "tags"]
        assert obsidian_repo._determine_note_type(tags) == NoteType.Literature

    def test_empty_tags(self, obsidian_repo):
        """空のタグリスト"""
        assert obsidian_repo._determine_note_type([]) == NoteType.Literature

    def test_first_matching_type_wins(self, obsidian_repo):
        """複数のタイプタグがある場合、最初にマッチしたものが優先"""
        # tag_to_type の順序に依存
        tags = ["obsidian/section/index", "obsidian/section/daily"]
        result = obsidian_repo._determine_note_type(tags)
        # Index が先に定義されているので Index が返る
        assert result == NoteType.Index


class TestParseFrontmatterFromContent:
    """_parse_frontmatter_from_content メソッドのテスト"""

    def test_valid_frontmatter(self, obsidian_repo, sample_note_content):
        """正常なFrontmatterをパース"""
        prop = obsidian_repo._parse_frontmatter_from_content(
            "test.md", sample_note_content
        )

        assert "obsidian/section/literature" in prop.tags
        assert "test" in prop.tags
        assert prop.title == "Sample Note"
        assert "サンプル" in prop.aliases
        assert prop.uid == "sample-001"

    def test_empty_frontmatter(self, obsidian_repo):
        """空のFrontmatter"""
        content = """---
---

Content here
"""
        prop = obsidian_repo._parse_frontmatter_from_content("test.md", content)

        assert prop.tags == []
        assert prop.title == ""
        assert prop.aliases == []
        assert prop.uid == ""

    def test_no_frontmatter(self, obsidian_repo):
        """Frontmatterがない場合"""
        content = "Just plain content without frontmatter"
        prop = obsidian_repo._parse_frontmatter_from_content("test.md", content)

        assert prop.tags == []
        assert prop.title == ""

    def test_partial_frontmatter(self, obsidian_repo):
        """一部のフィールドのみ"""
        content = """---
title: Only Title
---

Content
"""
        prop = obsidian_repo._parse_frontmatter_from_content("test.md", content)

        assert prop.title == "Only Title"
        assert prop.tags == []
        assert prop.uid == ""


class TestExtractContentBody:
    """_extract_content_body メソッドのテスト"""

    def test_with_frontmatter(self, obsidian_repo, sample_note_content):
        """Frontmatter付きコンテンツから本文を抽出"""
        body = obsidian_repo._extract_content_body("test.md", sample_note_content)

        assert body.startswith("# Sample Note")
        assert "This is a sample note content" in body
        assert "---" not in body.split("\n")[0]  # Frontmatter区切りが含まれない

    def test_without_frontmatter(self, obsidian_repo):
        """Frontmatterがない場合"""
        content = "Just plain content\n\nWith multiple lines"
        body = obsidian_repo._extract_content_body("test.md", content)

        assert body == content.strip()

    def test_empty_content(self, obsidian_repo):
        """空のコンテンツ"""
        body = obsidian_repo._extract_content_body("test.md", "")
        assert body == ""

    def test_frontmatter_only(self, obsidian_repo):
        """Frontmatterのみで本文なし"""
        content = """---
title: Title Only
---
"""
        body = obsidian_repo._extract_content_body("test.md", content)
        assert body == ""


# =============================================================================
# 統合テスト（ファイルシステム使用）
# =============================================================================


class TestObsidianRepositoryInit:
    """__init__ のテスト"""

    def test_valid_path(self, tmp_vault):
        """正常なパスで初期化"""
        repo = ObsidianRepository(str(tmp_vault))

        assert repo.obsidian_path == tmp_vault
        assert repo._cache == {}
        assert repo._cache_loaded is False

    def test_nonexistent_path(self, tmp_path):
        """存在しないパスでInvalidVaultPathErrorが発生"""
        nonexistent = tmp_path / "nonexistent"

        with pytest.raises(InvalidVaultPathError) as exc_info:
            ObsidianRepository(str(nonexistent))

        assert "nonexistent" in str(exc_info.value)

    def test_file_path_instead_of_directory(self, tmp_path):
        """ファイルパスを指定した場合InvalidVaultPathErrorが発生"""
        file_path = tmp_path / "file.txt"
        file_path.write_text("content")

        with pytest.raises(InvalidVaultPathError) as exc_info:
            ObsidianRepository(str(file_path))

        assert "ディレクトリではありません" in str(exc_info.value)


class TestGetAllNoteNames:
    """get_all_note_names のテスト"""

    def test_empty_vault(self, obsidian_repo):
        """空のVault"""
        names = obsidian_repo.get_all_note_names()
        assert names == []

    def test_with_md_files(self, tmp_vault, obsidian_repo):
        """複数の.mdファイル"""
        (tmp_vault / "note1.md").write_text("content1")
        (tmp_vault / "note2.md").write_text("content2")
        (tmp_vault / "not_md.txt").write_text("ignored")

        names = obsidian_repo.get_all_note_names()

        assert set(names) == {"note1.md", "note2.md"}
        assert "not_md.txt" not in names


class TestGetByFileName:
    """get_by_file_name のテスト"""

    def test_existing_file(self, obsidian_repo, sample_note_file):
        """存在するファイルを取得"""
        note = obsidian_repo.get_by_file_name("sample_note.md")

        assert note.name == "sample_note.md"
        assert note.properties.title == "Sample Note"
        assert "obsidian/section/literature" in note.properties.tags
        assert "Related Note" in note.links
        assert note.note_type == NoteType.Literature

    def test_nonexistent_file(self, obsidian_repo):
        """存在しないファイルでNoteNotFoundError"""
        with pytest.raises(NoteNotFoundError) as exc_info:
            obsidian_repo.get_by_file_name("nonexistent.md")

        assert "nonexistent.md" in str(exc_info.value)

    def test_cache_hit(self, obsidian_repo, sample_note_file):
        """キャッシュヒット"""
        # 1回目の読み込み
        note1 = obsidian_repo.get_by_file_name("sample_note.md")
        # 2回目はキャッシュから
        note2 = obsidian_repo.get_by_file_name("sample_note.md")

        assert note1 is note2  # 同じオブジェクト


class TestGetAllNotes:
    """get_all_notes のテスト"""

    def test_empty_vault(self, obsidian_repo):
        """空のVault"""
        notes = obsidian_repo.get_all_notes()
        assert notes == []

    def test_multiple_notes(
        self, tmp_vault, obsidian_repo, sample_note_content, sample_daily_note_content
    ):
        """複数のノート"""
        (tmp_vault / "note1.md").write_text(sample_note_content)
        (tmp_vault / "note2.md").write_text(sample_daily_note_content)

        notes = obsidian_repo.get_all_notes()

        assert len(notes) == 2
        names = [n.name for n in notes]
        assert "note1.md" in names
        assert "note2.md" in names

    def test_cache_loaded_flag(self, tmp_vault, obsidian_repo, sample_note_content):
        """キャッシュロードフラグ"""
        (tmp_vault / "note.md").write_text(sample_note_content)

        assert obsidian_repo._cache_loaded is False

        obsidian_repo.get_all_notes()

        assert obsidian_repo._cache_loaded is True


class TestFindByTag:
    """find_by_tag のテスト"""

    def test_find_matching_tag(
        self, tmp_vault, obsidian_repo, sample_note_content, sample_daily_note_content
    ):
        """タグでフィルタリング"""
        (tmp_vault / "lit.md").write_text(sample_note_content)
        (tmp_vault / "daily.md").write_text(sample_daily_note_content)

        notes = obsidian_repo.find_by_tag("test")

        assert len(notes) == 1
        assert notes[0].name == "lit.md"

    def test_no_matching_tag(self, tmp_vault, obsidian_repo, sample_note_content):
        """マッチしないタグ"""
        (tmp_vault / "note.md").write_text(sample_note_content)

        notes = obsidian_repo.find_by_tag("nonexistent_tag")

        assert notes == []


class TestFindByNoteType:
    """find_by_note_type のテスト"""

    def test_find_daily_notes(
        self, tmp_vault, obsidian_repo, sample_note_content, sample_daily_note_content
    ):
        """NoteTypeでフィルタリング"""
        (tmp_vault / "lit.md").write_text(sample_note_content)
        (tmp_vault / "daily.md").write_text(sample_daily_note_content)

        notes = obsidian_repo.find_by_note_type(NoteType.Daily)

        assert len(notes) == 1
        assert notes[0].note_type == NoteType.Daily

    def test_find_literature_notes(
        self, tmp_vault, obsidian_repo, sample_note_content, sample_daily_note_content
    ):
        """Literatureノートを検索"""
        (tmp_vault / "lit.md").write_text(sample_note_content)
        (tmp_vault / "daily.md").write_text(sample_daily_note_content)

        notes = obsidian_repo.find_by_note_type(NoteType.Literature)

        assert len(notes) == 1
        assert notes[0].note_type == NoteType.Literature


class TestSearchByText:
    """search_by_text のテスト"""

    def test_search_in_content(self, tmp_vault, obsidian_repo, sample_note_content):
        """本文内を検索"""
        (tmp_vault / "note.md").write_text(sample_note_content)

        notes = obsidian_repo.search_by_text("sample note content")

        assert len(notes) == 1

    def test_search_in_title(self, tmp_vault, obsidian_repo, sample_note_content):
        """タイトルを検索"""
        (tmp_vault / "note.md").write_text(sample_note_content)

        notes = obsidian_repo.search_by_text("Sample Note")

        assert len(notes) == 1

    def test_no_match(self, tmp_vault, obsidian_repo, sample_note_content):
        """マッチなし"""
        (tmp_vault / "note.md").write_text(sample_note_content)

        notes = obsidian_repo.search_by_text("completely unrelated text xyz")

        assert notes == []


class TestGetLinks:
    """get_links のテスト"""

    def test_get_existing_links(self, tmp_vault, obsidian_repo, sample_note_content):
        """存在するリンク先を取得"""
        (tmp_vault / "main.md").write_text(sample_note_content)
        (tmp_vault / "Related Note.md").write_text("---\ntitle: Related\n---\nContent")

        main_note = obsidian_repo.get_by_file_name("main.md")
        linked_notes = obsidian_repo.get_links(main_note)

        # Related Note.md は存在するので取得できる
        assert len(linked_notes) == 1
        assert linked_notes[0].name == "Related Note.md"

    def test_skip_nonexistent_links(
        self, tmp_vault, obsidian_repo, sample_note_content
    ):
        """存在しないリンク先はスキップ"""
        (tmp_vault / "main.md").write_text(sample_note_content)
        # Related Note.md は作成しない

        main_note = obsidian_repo.get_by_file_name("main.md")
        linked_notes = obsidian_repo.get_links(main_note)

        # 存在しないリンクはスキップされる
        assert linked_notes == []


class TestGetDailyNotes:
    """get_daily_notes のテスト"""

    def test_get_recent_daily_notes(
        self, tmp_vault, obsidian_repo, sample_daily_note_content
    ):
        """直近の日記を取得"""
        # 複数の日記を作成
        for i in range(5):
            content = sample_daily_note_content.replace(
                "2026-01-18", f"2026-01-{18 + i}"
            )
            (tmp_vault / f"daily_{i}.md").write_text(content)

        notes = obsidian_repo.get_daily_notes(3)

        assert len(notes) == 3

    def test_fewer_notes_than_requested(
        self, tmp_vault, obsidian_repo, sample_daily_note_content
    ):
        """リクエストより少ない場合"""
        (tmp_vault / "daily.md").write_text(sample_daily_note_content)

        notes = obsidian_repo.get_daily_notes(10)

        assert len(notes) == 1

    def test_notes_sorted_by_uid(
        self, tmp_vault, obsidian_repo, sample_daily_note_content
    ):
        """ノートがUID順にソートされる"""
        # 逆順でファイルを作成
        for i in [3, 1, 2]:
            content = sample_daily_note_content.replace(
                "daily-2026-01-18", f"daily-2026-01-{18 + i:02d}"
            ).replace("2026-01-18", f"2026-01-{18 + i:02d}")
            (tmp_vault / f"daily_{i}.md").write_text(content)

        notes = obsidian_repo.get_daily_notes(3)

        # 古い順にソートされている
        assert notes[0].properties.uid == "daily-2026-01-19"
        assert notes[1].properties.uid == "daily-2026-01-20"
        assert notes[2].properties.uid == "daily-2026-01-21"

    def test_exclude_today(self, tmp_vault, obsidian_repo, sample_daily_note_content):
        """exclude_today=True で当日のノートを除外"""
        from datetime import datetime
        from unittest.mock import patch

        # 当日の日付を固定
        with patch(
            "src.infrastructure.repositories.obsidian_repository.datetime"
        ) as mock_datetime:
            mock_datetime.now.return_value = datetime(2026, 1, 20)
            mock_datetime.strftime = datetime.strftime

            # 2026-01-19, 2026-01-20（当日）, 2026-01-21 のノートを作成
            for day in [19, 20, 21]:
                content = sample_daily_note_content.replace(
                    "daily-2026-01-18", f"2026-01-{day:02d}"
                ).replace("2026-01-18", f"2026-01-{day:02d}")
                (tmp_vault / f"daily_{day}.md").write_text(content)

            notes = obsidian_repo.get_daily_notes(10, exclude_today=True)

            # 当日（2026-01-20）が除外されている
            assert len(notes) == 2
            uids = [n.properties.uid for n in notes]
            assert "2026-01-20" not in uids

    def test_exclude_today_false(
        self, tmp_vault, obsidian_repo, sample_daily_note_content
    ):
        """exclude_today=False で当日のノートを含む"""
        from datetime import datetime
        from unittest.mock import patch

        with patch(
            "src.infrastructure.repositories.obsidian_repository.datetime"
        ) as mock_datetime:
            mock_datetime.now.return_value = datetime(2026, 1, 20)
            mock_datetime.strftime = datetime.strftime

            # 2026-01-19, 2026-01-20（当日）のノートを作成
            for day in [19, 20]:
                content = sample_daily_note_content.replace(
                    "daily-2026-01-18", f"2026-01-{day:02d}"
                ).replace("2026-01-18", f"2026-01-{day:02d}")
                (tmp_vault / f"daily_{day}.md").write_text(content)

            notes = obsidian_repo.get_daily_notes(10, exclude_today=False)

            assert len(notes) == 2


class TestSaveDailyNote:
    """save_daily_note のテスト"""

    def test_save_note(self, tmp_vault, obsidian_repo, sample_note):
        """ノートを保存"""
        obsidian_repo.save_daily_note(sample_note)

        # ファイルが作成されたことを確認
        md_files = list(tmp_vault.glob("*.md"))
        assert len(md_files) == 1

        # 内容を確認
        content = md_files[0].read_text()
        assert "tags:" in content
        assert "title:" in content
        assert sample_note.content in content

    def test_saved_note_in_cache(self, tmp_vault, obsidian_repo, sample_note):
        """保存したノートがキャッシュに追加される"""
        obsidian_repo.save_daily_note(sample_note)

        assert len(obsidian_repo._cache) == 1


class TestCacheOperations:
    """キャッシュ操作のテスト"""

    def test_refresh_cache(self, tmp_vault, obsidian_repo, sample_note_content):
        """キャッシュリフレッシュ"""
        (tmp_vault / "note.md").write_text(sample_note_content)

        # 最初の読み込み
        obsidian_repo.get_all_notes()
        assert obsidian_repo._cache_loaded is True

        # キャッシュをリフレッシュ
        obsidian_repo.refresh_cache()

        assert obsidian_repo._cache_loaded is True
        assert "note.md" in obsidian_repo._cache

    def test_clear_cache(self, tmp_vault, obsidian_repo, sample_note_content):
        """キャッシュクリア"""
        (tmp_vault / "note.md").write_text(sample_note_content)

        # キャッシュを構築
        obsidian_repo.get_all_notes()
        assert len(obsidian_repo._cache) > 0

        # キャッシュをクリア
        obsidian_repo.clear_cache()

        assert obsidian_repo._cache == {}
        assert obsidian_repo._cache_loaded is False
