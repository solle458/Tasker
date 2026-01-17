"""
domain/exceptions.py のテスト
"""

import pytest

from src.domain.exceptions import (
    NoteRepositoryError,
    NoteNotFoundError,
    NoteParseError,
    NoteIOError,
    InvalidVaultPathError,
)


class TestNoteRepositoryError:
    """NoteRepositoryError 基底例外のテスト"""

    def test_is_exception(self):
        """Exceptionを継承していることを確認"""
        assert issubclass(NoteRepositoryError, Exception)

    def test_can_be_raised(self):
        """例外として発生できることを確認"""
        with pytest.raises(NoteRepositoryError):
            raise NoteRepositoryError("Test error")


class TestNoteNotFoundError:
    """NoteNotFoundError のテスト"""

    def test_inherits_from_base(self):
        """NoteRepositoryErrorを継承していることを確認"""
        assert issubclass(NoteNotFoundError, NoteRepositoryError)

    def test_with_file_name_only(self):
        """ファイル名のみでインスタンス化"""
        error = NoteNotFoundError("test.md")

        assert error.file_name == "test.md"
        assert "test.md" in error.message
        assert "test.md" in str(error)

    def test_with_custom_message(self):
        """カスタムメッセージでインスタンス化"""
        error = NoteNotFoundError("test.md", "カスタムエラーメッセージ")

        assert error.file_name == "test.md"
        assert error.message == "カスタムエラーメッセージ"
        assert str(error) == "カスタムエラーメッセージ"

    def test_default_message_generated(self):
        """デフォルトメッセージが生成されることを確認"""
        error = NoteNotFoundError("missing.md")

        assert "ノートが見つかりません" in error.message
        assert "missing.md" in error.message


class TestNoteParseError:
    """NoteParseError のテスト"""

    def test_inherits_from_base(self):
        """NoteRepositoryErrorを継承していることを確認"""
        assert issubclass(NoteParseError, NoteRepositoryError)

    def test_with_file_name_only(self):
        """ファイル名のみでインスタンス化"""
        error = NoteParseError("test.md")

        assert error.file_name == "test.md"
        assert error.original_error is None
        assert "test.md" in error.message

    def test_with_original_error(self):
        """元の例外を保持できることを確認"""
        original = ValueError("YAML parse error")
        error = NoteParseError("test.md", original_error=original)

        assert error.original_error is original
        assert isinstance(error.original_error, ValueError)

    def test_with_custom_message_and_original_error(self):
        """カスタムメッセージと元の例外を設定"""
        original = SyntaxError("Invalid syntax")
        error = NoteParseError(
            "test.md", message="Frontmatterのパースに失敗", original_error=original
        )

        assert error.file_name == "test.md"
        assert error.message == "Frontmatterのパースに失敗"
        assert error.original_error is original

    def test_default_message_generated(self):
        """デフォルトメッセージが生成されることを確認"""
        error = NoteParseError("broken.md")

        assert "パースに失敗" in error.message
        assert "broken.md" in error.message


class TestNoteIOError:
    """NoteIOError のテスト"""

    def test_inherits_from_base(self):
        """NoteRepositoryErrorを継承していることを確認"""
        assert issubclass(NoteIOError, NoteRepositoryError)

    def test_with_file_path_only(self):
        """ファイルパスのみでインスタンス化"""
        error = NoteIOError("/path/to/file.md")

        assert error.file_path == "/path/to/file.md"
        assert error.original_error is None
        assert "/path/to/file.md" in error.message

    def test_with_original_error(self):
        """元の例外を保持できることを確認"""
        original = PermissionError("Permission denied")
        error = NoteIOError("/path/to/file.md", original_error=original)

        assert error.original_error is original
        assert isinstance(error.original_error, PermissionError)

    def test_with_all_arguments(self):
        """全ての引数を設定"""
        original = OSError("Disk full")
        error = NoteIOError(
            "/vault/note.md", message="ディスク容量不足", original_error=original
        )

        assert error.file_path == "/vault/note.md"
        assert error.message == "ディスク容量不足"
        assert error.original_error is original

    def test_default_message_generated(self):
        """デフォルトメッセージが生成されることを確認"""
        error = NoteIOError("/some/path.md")

        assert "I/O" in error.message or "ファイル" in error.message
        assert "/some/path.md" in error.message


class TestInvalidVaultPathError:
    """InvalidVaultPathError のテスト"""

    def test_inherits_from_base(self):
        """NoteRepositoryErrorを継承していることを確認"""
        assert issubclass(InvalidVaultPathError, NoteRepositoryError)

    def test_with_vault_path_only(self):
        """Vaultパスのみでインスタンス化"""
        error = InvalidVaultPathError("/invalid/vault/path")

        assert error.vault_path == "/invalid/vault/path"
        assert "/invalid/vault/path" in error.message

    def test_with_custom_message(self):
        """カスタムメッセージでインスタンス化"""
        error = InvalidVaultPathError(
            "/nonexistent", "指定されたディレクトリは存在しません"
        )

        assert error.vault_path == "/nonexistent"
        assert error.message == "指定されたディレクトリは存在しません"

    def test_default_message_generated(self):
        """デフォルトメッセージが生成されることを確認"""
        error = InvalidVaultPathError("/bad/path")

        assert "Vault" in error.message or "無効" in error.message
        assert "/bad/path" in error.message


class TestExceptionHierarchy:
    """例外の継承階層のテスト"""

    def test_all_exceptions_inherit_from_base(self):
        """全てのカスタム例外がNoteRepositoryErrorを継承していることを確認"""
        exception_classes = [
            NoteNotFoundError,
            NoteParseError,
            NoteIOError,
            InvalidVaultPathError,
        ]

        for exc_class in exception_classes:
            assert issubclass(exc_class, NoteRepositoryError), (
                f"{exc_class.__name__} should inherit from NoteRepositoryError"
            )

    def test_can_catch_all_with_base(self):
        """基底例外で全てのカスタム例外をキャッチできることを確認"""
        exceptions_to_raise = [
            NoteNotFoundError("file.md"),
            NoteParseError("file.md"),
            NoteIOError("/path/file.md"),
            InvalidVaultPathError("/path"),
        ]

        for exc in exceptions_to_raise:
            with pytest.raises(NoteRepositoryError):
                raise exc
