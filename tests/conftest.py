"""
pytest 共通フィクスチャ
"""

import pytest
from pathlib import Path

from src.infrastructure.repositories.obsidian_repository import ObsidianRepository
from src.domain.models.note import Note, NoteType, Property


@pytest.fixture
def tmp_vault(tmp_path: Path) -> Path:
    """一時的なVaultディレクトリを作成する

    Returns:
        Path: 作成されたVaultディレクトリのパス
    """
    vault = tmp_path / "vault"
    vault.mkdir()
    return vault


@pytest.fixture
def obsidian_repo(tmp_vault: Path) -> ObsidianRepository:
    """テスト用のObsidianRepositoryインスタンスを作成する

    Args:
        tmp_vault: 一時的なVaultディレクトリ

    Returns:
        ObsidianRepository: テスト用インスタンス
    """
    return ObsidianRepository(str(tmp_vault))


@pytest.fixture
def sample_note_content() -> str:
    """サンプルノートのコンテンツ（Frontmatter付き）

    Returns:
        str: サンプルノートの内容
    """
    return """---
tags:
  - obsidian/section/literature
  - test
title: Sample Note
aliases:
  - サンプル
uid: sample-001
---

# Sample Note

This is a sample note content.

See also [[Related Note]] and [[Another Note|alias]].

## Section 1

Some more content here.
"""


@pytest.fixture
def sample_daily_note_content() -> str:
    """サンプル日記ノートのコンテンツ

    Returns:
        str: サンプル日記ノートの内容
    """
    return """---
tags:
  - obsidian/section/daily
title: Daily Note 2026-01-18
aliases: []
uid: daily-2026-01-18
---

# 2026-01-18

## Today's Tasks

- Task 1
- Task 2
"""


@pytest.fixture
def sample_note_file(tmp_vault: Path, sample_note_content: str) -> Path:
    """サンプルノートファイルを作成する

    Args:
        tmp_vault: Vaultディレクトリ
        sample_note_content: ノートの内容

    Returns:
        Path: 作成されたファイルのパス
    """
    note_path = tmp_vault / "sample_note.md"
    note_path.write_text(sample_note_content, encoding="utf-8")
    return note_path


@pytest.fixture
def sample_daily_note_file(tmp_vault: Path, sample_daily_note_content: str) -> Path:
    """サンプル日記ノートファイルを作成する

    Args:
        tmp_vault: Vaultディレクトリ
        sample_daily_note_content: ノートの内容

    Returns:
        Path: 作成されたファイルのパス
    """
    note_path = tmp_vault / "2026-01-18.md"
    note_path.write_text(sample_daily_note_content, encoding="utf-8")
    return note_path


@pytest.fixture
def sample_property() -> Property:
    """サンプルPropertyインスタンス

    Returns:
        Property: テスト用Propertyインスタンス
    """
    return Property(
        tags=["obsidian/section/literature", "test"],
        title="Sample Note",
        aliases=["サンプル"],
        uid="sample-001",
    )


@pytest.fixture
def sample_note(sample_property: Property) -> Note:
    """サンプルNoteインスタンス

    Args:
        sample_property: Propertyインスタンス

    Returns:
        Note: テスト用Noteインスタンス
    """
    return Note(
        name="sample_note.md",
        properties=sample_property,
        content="# Sample Note\n\nThis is a sample note.",
        links=["Related Note", "Another Note"],
        note_type=NoteType.Literature,
    )
