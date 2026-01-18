"""
domain/models/note.py のテスト
"""

import re

from src.domain.models.note import Note, NoteType, Property


class TestNoteType:
    """NoteType Enum のテスト"""

    def test_all_note_types_exist(self):
        """全てのNoteType値が存在することを確認"""
        expected_types = [
            "Index",
            "Structure",
            "Daily",
            "Literature",
            "Fleeting",
            "Permanent",
        ]
        actual_types = [t.name for t in NoteType]
        assert set(actual_types) == set(expected_types)

    def test_note_type_values_are_unique(self):
        """NoteTypeの値が重複していないことを確認"""
        values = [t.value for t in NoteType]
        assert len(values) == len(set(values))

    def test_note_type_count(self):
        """NoteTypeの数が正しいことを確認"""
        assert len(NoteType) == 6


class TestProperty:
    """Property dataclass のテスト"""

    def test_default_values(self):
        """デフォルト値でインスタンス化できることを確認"""
        prop = Property()
        assert prop.tags == []
        assert prop.title == ""
        assert prop.aliases == []
        assert prop.uid == ""

    def test_with_arguments(self):
        """引数を指定してインスタンス化できることを確認"""
        prop = Property(
            tags=["tag1", "tag2"],
            title="Test Title",
            aliases=["alias1", "alias2"],
            uid="test-uid-123",
        )
        assert prop.tags == ["tag1", "tag2"]
        assert prop.title == "Test Title"
        assert prop.aliases == ["alias1", "alias2"]
        assert prop.uid == "test-uid-123"

    def test_mutable_default_not_shared(self):
        """ミュータブルなデフォルト値（list）が共有されないことを確認"""
        prop1 = Property()
        prop2 = Property()

        prop1.tags.append("new_tag")

        # prop2のtagsには影響しないことを確認
        assert "new_tag" not in prop2.tags
        assert prop1.tags != prop2.tags

    def test_aliases_mutable_default_not_shared(self):
        """aliasesのミュータブルなデフォルト値が共有されないことを確認"""
        prop1 = Property()
        prop2 = Property()

        prop1.aliases.append("new_alias")

        assert "new_alias" not in prop2.aliases


class TestNote:
    """Note dataclass のテスト"""

    def test_default_values(self):
        """デフォルト値でインスタンス化できることを確認"""
        note = Note()

        assert note.properties.tags == []
        assert note.properties.title == ""
        assert note.content == ""
        assert note.links == []
        assert note.note_type == NoteType.Literature

    def test_default_name_format(self):
        """デフォルトのnameが日時フォーマットになっていることを確認"""
        note = Note()

        # フォーマット: %Y-%m-%dT%H-%M-%S.md (ISO 8601形式)
        pattern = r"^\d{4}-\d{2}-\d{2}T\d{2}-\d{2}-\d{2}\.md$"
        assert re.match(pattern, note.name) is not None

    def test_with_arguments(self):
        """引数を指定してインスタンス化できることを確認"""
        prop = Property(tags=["test"], title="Test Note", aliases=[], uid="test-001")
        note = Note(
            name="test_note.md",
            properties=prop,
            content="Test content",
            links=["link1", "link2"],
            note_type=NoteType.Daily,
        )

        assert note.name == "test_note.md"
        assert note.properties.title == "Test Note"
        assert note.content == "Test content"
        assert note.links == ["link1", "link2"]
        assert note.note_type == NoteType.Daily

    def test_with_sample_note_fixture(self, sample_note):
        """フィクスチャを使用したテスト"""
        assert sample_note.name == "sample_note.md"
        assert sample_note.note_type == NoteType.Literature
        assert "Related Note" in sample_note.links

    def test_links_mutable_default_not_shared(self):
        """linksのミュータブルなデフォルト値が共有されないことを確認"""
        note1 = Note()
        note2 = Note()

        note1.links.append("new_link")

        assert "new_link" not in note2.links

    def test_note_type_assignment(self):
        """各NoteTypeを正しく設定できることを確認"""
        for note_type in NoteType:
            note = Note(note_type=note_type)
            assert note.note_type == note_type
