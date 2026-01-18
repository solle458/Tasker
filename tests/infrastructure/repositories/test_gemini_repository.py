"""
infrastructure/repositories/gemini_repository.py のテスト
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime

from src.infrastructure.repositories.gemini_repository import GeminiRepository
from src.infrastructure.config import GeminiConfig
from src.domain.models.task import TaskType
from src.domain.models.note import Note, NoteType, Property
from src.domain.models.calendar import Event
from src.domain.models.context import InitialContext, NoteMetadata


# =============================================================================
# フィクスチャ
# =============================================================================


@pytest.fixture
def mock_gemini_config(tmp_path):
    """テスト用のGeminiConfig"""
    prompt_path = tmp_path / "test_prompt.md"
    prompt_path.write_text("# Test Prompt\n\nGenerate tasks based on the input.")

    return GeminiConfig(
        api_key="test_api_key",
        model="gemini-test-model",
        prompt_path=str(prompt_path),
        max_tool_calls=10,
    )


@pytest.fixture
def mock_note_repository():
    """モックノートリポジトリ"""
    return Mock()


@pytest.fixture
def sample_note():
    """サンプルノート"""
    prop = Property(
        tags=["obsidian/section/literature", "project/test"],
        title="テストノート",
        aliases=[],
        uid="test-001",
    )
    return Note(
        name="test_note.md",
        properties=prop,
        content="# テストノート\n\nこれはテスト用のノートコンテンツです。" * 10,
        links=["Related-Note.md"],
        note_type=NoteType.Literature,
    )


@pytest.fixture
def sample_index_note():
    """サンプルIndexノート"""
    prop = Property(
        tags=["obsidian/section/index"],
        title="Index Note",
        aliases=[],
        uid="index-001",
    )
    return Note(
        name="Index.md",
        properties=prop,
        content="# 長期目標\n\n- 目標1\n- 目標2",
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
            title=f"Daily Note 2026-01-{15 + i}",
            aliases=[],
            uid=f"daily-{i}",
        )
        note = Note(
            name=f"2026-01-{15 + i}.md",
            properties=prop,
            content=f"# 2026-01-{15 + i}\n\n## Task\n- タスク{i}",
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


@pytest.fixture
def sample_initial_context(sample_index_note, sample_daily_notes, sample_events):
    """サンプル初期コンテキスト"""
    return InitialContext(
        index_notes=[sample_index_note],
        weekly_daily_notes=sample_daily_notes,
        events=sample_events,
        achievement_rate=0.8,
        note_metadata_list=[
            NoteMetadata.from_note(sample_index_note),
            *[NoteMetadata.from_note(n) for n in sample_daily_notes],
        ],
    )


@pytest.fixture
def valid_json_response():
    """有効なJSONレスポンス"""
    return """```json
{
  "tasks": [
    {"name": "朝会に参加", "task_type": "Daily"},
    {"name": "プロジェクト資料準備", "task_type": "Must"},
    {"name": "メール確認", "task_type": "Should"},
    {"name": "読書", "task_type": "Could"}
  ]
}
```"""


@pytest.fixture
def valid_json_response_no_fence():
    """フェンスなしの有効なJSONレスポンス"""
    return """{
  "tasks": [
    {"name": "タスク1", "task_type": "Must"},
    {"name": "タスク2", "task_type": "Should"}
  ]
}"""


@pytest.fixture
def invalid_json_response():
    """無効なJSONレスポンス"""
    return "This is not valid JSON at all"


@pytest.fixture
def empty_tasks_response():
    """空のタスク配列を持つJSONレスポンス"""
    return """```json
{
  "tasks": []
}
```"""


# =============================================================================
# _parse_tasks_from_json メソッドテスト
# =============================================================================


class TestParseTasksFromJson:
    """_parse_tasks_from_json メソッドのテスト"""

    @patch("src.infrastructure.repositories.gemini_repository.genai.Client")
    def test_parse_valid_json_with_fence(
        self,
        mock_client_class,
        mock_gemini_config,
        mock_note_repository,
        valid_json_response,
    ):
        """フェンス付きの有効なJSONをパース"""
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        repo = GeminiRepository(mock_gemini_config, mock_note_repository)
        tasks = repo._parse_tasks_from_json(valid_json_response)

        assert len(tasks) == 4
        assert tasks[0].name == "朝会に参加"
        assert tasks[0].task_type == TaskType.Daily
        assert tasks[1].name == "プロジェクト資料準備"
        assert tasks[1].task_type == TaskType.Must
        assert tasks[2].name == "メール確認"
        assert tasks[2].task_type == TaskType.Should
        assert tasks[3].name == "読書"
        assert tasks[3].task_type == TaskType.Could

    @patch("src.infrastructure.repositories.gemini_repository.genai.Client")
    def test_parse_valid_json_without_fence(
        self,
        mock_client_class,
        mock_gemini_config,
        mock_note_repository,
        valid_json_response_no_fence,
    ):
        """フェンスなしの有効なJSONをパース"""
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        repo = GeminiRepository(mock_gemini_config, mock_note_repository)
        tasks = repo._parse_tasks_from_json(valid_json_response_no_fence)

        assert len(tasks) == 2
        assert tasks[0].name == "タスク1"
        assert tasks[0].task_type == TaskType.Must
        assert tasks[1].name == "タスク2"
        assert tasks[1].task_type == TaskType.Should

    @patch("src.infrastructure.repositories.gemini_repository.genai.Client")
    def test_parse_invalid_json(
        self,
        mock_client_class,
        mock_gemini_config,
        mock_note_repository,
        invalid_json_response,
    ):
        """無効なJSONをパースした場合は空リストを返す"""
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        repo = GeminiRepository(mock_gemini_config, mock_note_repository)
        tasks = repo._parse_tasks_from_json(invalid_json_response)

        assert tasks == []

    @patch("src.infrastructure.repositories.gemini_repository.genai.Client")
    def test_parse_empty_tasks(
        self,
        mock_client_class,
        mock_gemini_config,
        mock_note_repository,
        empty_tasks_response,
    ):
        """空のタスク配列をパース"""
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        repo = GeminiRepository(mock_gemini_config, mock_note_repository)
        tasks = repo._parse_tasks_from_json(empty_tasks_response)

        assert tasks == []

    @patch("src.infrastructure.repositories.gemini_repository.genai.Client")
    def test_parse_unknown_task_type_defaults_to_daily(
        self, mock_client_class, mock_gemini_config, mock_note_repository
    ):
        """不明なtask_typeはDailyにデフォルト"""
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        response = """```json
{
  "tasks": [
    {"name": "不明タイプのタスク", "task_type": "Unknown"}
  ]
}
```"""

        repo = GeminiRepository(mock_gemini_config, mock_note_repository)
        tasks = repo._parse_tasks_from_json(response)

        assert len(tasks) == 1
        assert tasks[0].task_type == TaskType.Daily

    @patch("src.infrastructure.repositories.gemini_repository.genai.Client")
    def test_parse_all_tasks_have_is_completed_false(
        self,
        mock_client_class,
        mock_gemini_config,
        mock_note_repository,
        valid_json_response,
    ):
        """全てのタスクのis_completedがFalseであることを確認"""
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        repo = GeminiRepository(mock_gemini_config, mock_note_repository)
        tasks = repo._parse_tasks_from_json(valid_json_response)

        assert all(task.is_completed is False for task in tasks)


# =============================================================================
# ツール実行テスト
# =============================================================================


class TestToolExecution:
    """ツール実行のテスト"""

    @patch("src.infrastructure.repositories.gemini_repository.genai.Client")
    def test_tool_read_note_success(
        self,
        mock_client_class,
        mock_gemini_config,
        mock_note_repository,
        sample_note,
    ):
        """read_note ツールの正常実行"""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_note_repository.get_by_file_name.return_value = sample_note

        repo = GeminiRepository(mock_gemini_config, mock_note_repository)
        result = repo._tool_read_note("test_note.md")

        assert result["name"] == "test_note.md"
        assert result["title"] == "テストノート"
        assert "obsidian/section/literature" in result["tags"]
        mock_note_repository.get_by_file_name.assert_called_once_with("test_note.md")

    @patch("src.infrastructure.repositories.gemini_repository.genai.Client")
    def test_tool_read_note_not_found(
        self, mock_client_class, mock_gemini_config, mock_note_repository
    ):
        """read_note ツールでノートが見つからない場合"""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_note_repository.get_by_file_name.return_value = None

        repo = GeminiRepository(mock_gemini_config, mock_note_repository)
        result = repo._tool_read_note("nonexistent.md")

        assert "error" in result

    @patch("src.infrastructure.repositories.gemini_repository.genai.Client")
    def test_tool_find_notes_by_tag(
        self,
        mock_client_class,
        mock_gemini_config,
        mock_note_repository,
        sample_note,
    ):
        """find_notes_by_tag ツールの実行"""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_note_repository.find_by_tag.return_value = [sample_note]

        repo = GeminiRepository(mock_gemini_config, mock_note_repository)
        result = repo._tool_find_notes_by_tag("project/test")

        assert result["count"] == 1
        assert len(result["notes"]) == 1
        mock_note_repository.find_by_tag.assert_called_once_with("project/test")

    @patch("src.infrastructure.repositories.gemini_repository.genai.Client")
    def test_tool_find_notes_by_type(
        self,
        mock_client_class,
        mock_gemini_config,
        mock_note_repository,
        sample_index_note,
    ):
        """find_notes_by_type ツールの実行"""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_note_repository.find_by_note_type.return_value = [sample_index_note]

        repo = GeminiRepository(mock_gemini_config, mock_note_repository)
        result = repo._tool_find_notes_by_type("Index")

        assert result["count"] == 1
        mock_note_repository.find_by_note_type.assert_called_once_with(NoteType.Index)

    @patch("src.infrastructure.repositories.gemini_repository.genai.Client")
    def test_tool_find_notes_by_type_invalid(
        self, mock_client_class, mock_gemini_config, mock_note_repository
    ):
        """find_notes_by_type ツールで無効なタイプを指定した場合"""
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        repo = GeminiRepository(mock_gemini_config, mock_note_repository)
        result = repo._tool_find_notes_by_type("InvalidType")

        assert "error" in result

    @patch("src.infrastructure.repositories.gemini_repository.genai.Client")
    def test_tool_get_note_links(
        self,
        mock_client_class,
        mock_gemini_config,
        mock_note_repository,
        sample_note,
    ):
        """get_note_links ツールの実行"""
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        linked_note = Note(
            name="Related-Note.md",
            properties=Property(tags=[], title="関連ノート"),
            content="関連内容",
            links=[],
            note_type=NoteType.Literature,
        )
        mock_note_repository.get_by_file_name.return_value = sample_note
        mock_note_repository.get_links.return_value = [linked_note]

        repo = GeminiRepository(mock_gemini_config, mock_note_repository)
        result = repo._tool_get_note_links("test_note.md")

        assert result["source"] == "test_note.md"
        assert result["count"] == 1

    @patch("src.infrastructure.repositories.gemini_repository.genai.Client")
    def test_tool_search_notes(
        self,
        mock_client_class,
        mock_gemini_config,
        mock_note_repository,
        sample_note,
    ):
        """search_notes ツールの実行"""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_note_repository.search_by_text.return_value = [sample_note]

        repo = GeminiRepository(mock_gemini_config, mock_note_repository)
        result = repo._tool_search_notes("テスト")

        assert result["query"] == "テスト"
        assert result["count"] == 1
        mock_note_repository.search_by_text.assert_called_once_with("テスト")


# =============================================================================
# generate_tasks メソッドテスト
# =============================================================================


class TestGenerateTasks:
    """generate_tasks メソッドのテスト"""

    @patch("src.infrastructure.repositories.gemini_repository.genai.Client")
    def test_generate_tasks_no_function_calls(
        self,
        mock_client_class,
        mock_gemini_config,
        mock_note_repository,
        sample_initial_context,
        valid_json_response,
    ):
        """Function Call なしでタスクを生成"""
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        # レスポンスのモック（Function Call なし）
        mock_response = Mock()
        mock_response.function_calls = None
        mock_response.text = valid_json_response
        mock_response.candidates = [Mock(content=Mock())]
        mock_client.models.generate_content.return_value = mock_response

        repo = GeminiRepository(mock_gemini_config, mock_note_repository)
        tasks = repo.generate_tasks(sample_initial_context)

        assert len(tasks) == 4
        assert tasks[0].name == "朝会に参加"

    @patch("src.infrastructure.repositories.gemini_repository.genai.Client")
    def test_generate_tasks_with_function_call(
        self,
        mock_client_class,
        mock_gemini_config,
        mock_note_repository,
        sample_initial_context,
        sample_note,
        valid_json_response,
    ):
        """Function Call ありでタスクを生成"""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_note_repository.get_by_file_name.return_value = sample_note

        # 1回目のレスポンス（Function Call あり）
        mock_fn_call = Mock()
        mock_fn_call.name = "read_note"
        mock_fn_call.args = {"note_name": "test_note.md"}

        mock_response_1 = Mock()
        mock_response_1.function_calls = [mock_fn_call]
        mock_response_1.candidates = [Mock(content=Mock())]

        # 2回目のレスポンス（最終回答）
        mock_response_2 = Mock()
        mock_response_2.function_calls = None
        mock_response_2.text = valid_json_response
        mock_response_2.candidates = [Mock(content=Mock())]

        mock_client.models.generate_content.side_effect = [
            mock_response_1,
            mock_response_2,
        ]

        repo = GeminiRepository(mock_gemini_config, mock_note_repository)
        tasks = repo.generate_tasks(sample_initial_context)

        assert len(tasks) == 4
        # ツールが呼ばれたことを確認
        mock_note_repository.get_by_file_name.assert_called_with("test_note.md")

    @patch("src.infrastructure.repositories.gemini_repository.genai.Client")
    def test_generate_tasks_max_tool_calls_limit(
        self,
        mock_client_class,
        mock_gemini_config,
        mock_note_repository,
        sample_initial_context,
        sample_note,
        valid_json_response,
    ):
        """最大ツール呼び出し回数制限のテスト"""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_note_repository.get_by_file_name.return_value = sample_note

        # 常に Function Call を返すレスポンス
        mock_fn_call = Mock()
        mock_fn_call.name = "read_note"
        mock_fn_call.args = {"note_name": "test_note.md"}

        mock_response = Mock()
        mock_response.function_calls = [mock_fn_call]
        mock_response.text = valid_json_response
        mock_response.candidates = [Mock(content=Mock())]

        mock_client.models.generate_content.return_value = mock_response

        # max_tool_calls を 3 に設定
        mock_gemini_config.max_tool_calls = 3

        repo = GeminiRepository(mock_gemini_config, mock_note_repository)
        repo.generate_tasks(sample_initial_context)

        # 最大回数（3回）で停止することを確認
        # 初回呼び出し + ツール結果を返す呼び出し = 3回
        assert mock_client.models.generate_content.call_count == 3


# =============================================================================
# 初期化テスト
# =============================================================================


class TestGeminiRepositoryInit:
    """GeminiRepository 初期化のテスト"""

    @patch("src.infrastructure.repositories.gemini_repository.genai.Client")
    def test_init_with_config(
        self, mock_client_class, mock_gemini_config, mock_note_repository
    ):
        """設定を指定して初期化"""
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        repo = GeminiRepository(mock_gemini_config, mock_note_repository)

        assert repo.config == mock_gemini_config
        assert repo.note_repository == mock_note_repository
        mock_client_class.assert_called_once_with(api_key="test_api_key")

    @patch("src.infrastructure.repositories.gemini_repository.genai.Client")
    def test_init_creates_client(
        self, mock_client_class, mock_gemini_config, mock_note_repository
    ):
        """クライアントが作成されることを確認"""
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        repo = GeminiRepository(mock_gemini_config, mock_note_repository)

        assert repo.client == mock_client


# =============================================================================
# ツール宣言テスト
# =============================================================================


class TestToolDeclarations:
    """ツール宣言のテスト"""

    @patch("src.infrastructure.repositories.gemini_repository.genai.Client")
    def test_get_tool_declarations_count(
        self, mock_client_class, mock_gemini_config, mock_note_repository
    ):
        """5つのツールが定義されていることを確認"""
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        repo = GeminiRepository(mock_gemini_config, mock_note_repository)
        declarations = repo._get_tool_declarations()

        assert len(declarations) == 5

    @patch("src.infrastructure.repositories.gemini_repository.genai.Client")
    def test_get_tool_declarations_names(
        self, mock_client_class, mock_gemini_config, mock_note_repository
    ):
        """正しいツール名が定義されていることを確認"""
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        repo = GeminiRepository(mock_gemini_config, mock_note_repository)
        declarations = repo._get_tool_declarations()

        tool_names = [d.name for d in declarations]
        assert "read_note" in tool_names
        assert "find_notes_by_tag" in tool_names
        assert "find_notes_by_type" in tool_names
        assert "get_note_links" in tool_names
        assert "search_notes" in tool_names
