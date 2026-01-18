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
    )


@pytest.fixture
def sample_notes():
    """サンプルノートリスト"""
    prop = Property(
        tags=["obsidian/section/literature"],
        title="テストノート",
        aliases=[],
        uid="test-001",
    )
    return [
        Note(
            name="test_note.md",
            properties=prop,
            content="# テストノート\n\nこれはテスト用のノートコンテンツです。" * 10,
            links=[],
            note_type=NoteType.Literature,
        )
    ]


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
# _format メソッドテスト
# =============================================================================


class TestFormat:
    """_format メソッドのテスト"""

    @patch("src.infrastructure.repositories.gemini_repository.genai.Client")
    def test_format_with_data(
        self, mock_client_class, mock_gemini_config, sample_notes, sample_events
    ):
        """データありでフォーマット"""
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        repo = GeminiRepository(mock_gemini_config)
        result = repo._format(
            arhievment_rate=0.8,
            relevant_notes=sample_notes,
            events=sample_events,
        )

        # 達成率が含まれていることを確認
        assert "80.0%" in result
        # ノート情報が含まれていることを確認
        assert "テストノート" in result
        # イベント情報が含まれていることを確認
        assert "朝会" in result
        assert "プロジェクト会議" in result
        # JSON出力形式の指示が含まれていることを確認
        assert "JSON" in result
        assert "task_type" in result

    @patch("src.infrastructure.repositories.gemini_repository.genai.Client")
    def test_format_with_empty_notes(
        self, mock_client_class, mock_gemini_config, sample_events
    ):
        """空のノートリストでフォーマット"""
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        repo = GeminiRepository(mock_gemini_config)
        result = repo._format(
            arhievment_rate=0.5,
            relevant_notes=[],
            events=sample_events,
        )

        # 「なし」が含まれていることを確認
        assert "なし" in result
        # イベント情報は含まれている
        assert "朝会" in result

    @patch("src.infrastructure.repositories.gemini_repository.genai.Client")
    def test_format_with_empty_events(
        self, mock_client_class, mock_gemini_config, sample_notes
    ):
        """空のイベントリストでフォーマット"""
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        repo = GeminiRepository(mock_gemini_config)
        result = repo._format(
            arhievment_rate=0.6,
            relevant_notes=sample_notes,
            events=[],
        )

        # イベント部分に「なし」が含まれていることを確認
        assert "今日の予定:" in result
        # ノート情報は含まれている
        assert "テストノート" in result

    @patch("src.infrastructure.repositories.gemini_repository.genai.Client")
    def test_format_with_zero_achievement_rate(
        self, mock_client_class, mock_gemini_config, sample_notes, sample_events
    ):
        """達成率0でフォーマット"""
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        repo = GeminiRepository(mock_gemini_config)
        result = repo._format(
            arhievment_rate=0.0,
            relevant_notes=sample_notes,
            events=sample_events,
        )

        assert "0.0%" in result

    @patch("src.infrastructure.repositories.gemini_repository.genai.Client")
    def test_format_with_full_achievement_rate(
        self, mock_client_class, mock_gemini_config, sample_notes, sample_events
    ):
        """達成率100%でフォーマット"""
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        repo = GeminiRepository(mock_gemini_config)
        result = repo._format(
            arhievment_rate=1.0,
            relevant_notes=sample_notes,
            events=sample_events,
        )

        assert "100.0%" in result


# =============================================================================
# _parse_tasks_from_json メソッドテスト
# =============================================================================


class TestParseTasksFromJson:
    """_parse_tasks_from_json メソッドのテスト"""

    @patch("src.infrastructure.repositories.gemini_repository.genai.Client")
    def test_parse_valid_json_with_fence(
        self, mock_client_class, mock_gemini_config, valid_json_response
    ):
        """フェンス付きの有効なJSONをパース"""
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        repo = GeminiRepository(mock_gemini_config)
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
        self, mock_client_class, mock_gemini_config, valid_json_response_no_fence
    ):
        """フェンスなしの有効なJSONをパース"""
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        repo = GeminiRepository(mock_gemini_config)
        tasks = repo._parse_tasks_from_json(valid_json_response_no_fence)

        assert len(tasks) == 2
        assert tasks[0].name == "タスク1"
        assert tasks[0].task_type == TaskType.Must
        assert tasks[1].name == "タスク2"
        assert tasks[1].task_type == TaskType.Should

    @patch("src.infrastructure.repositories.gemini_repository.genai.Client")
    def test_parse_invalid_json(
        self, mock_client_class, mock_gemini_config, invalid_json_response
    ):
        """無効なJSONをパースした場合は空リストを返す"""
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        repo = GeminiRepository(mock_gemini_config)
        tasks = repo._parse_tasks_from_json(invalid_json_response)

        assert tasks == []

    @patch("src.infrastructure.repositories.gemini_repository.genai.Client")
    def test_parse_empty_tasks(
        self, mock_client_class, mock_gemini_config, empty_tasks_response
    ):
        """空のタスク配列をパース"""
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        repo = GeminiRepository(mock_gemini_config)
        tasks = repo._parse_tasks_from_json(empty_tasks_response)

        assert tasks == []

    @patch("src.infrastructure.repositories.gemini_repository.genai.Client")
    def test_parse_unknown_task_type_defaults_to_daily(
        self, mock_client_class, mock_gemini_config
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

        repo = GeminiRepository(mock_gemini_config)
        tasks = repo._parse_tasks_from_json(response)

        assert len(tasks) == 1
        assert tasks[0].task_type == TaskType.Daily

    @patch("src.infrastructure.repositories.gemini_repository.genai.Client")
    def test_parse_missing_task_type_defaults_to_daily(
        self, mock_client_class, mock_gemini_config
    ):
        """task_typeがない場合はDailyにデフォルト"""
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        response = """```json
{
  "tasks": [
    {"name": "タイプなしタスク"}
  ]
}
```"""

        repo = GeminiRepository(mock_gemini_config)
        tasks = repo._parse_tasks_from_json(response)

        assert len(tasks) == 1
        assert tasks[0].name == "タイプなしタスク"
        assert tasks[0].task_type == TaskType.Daily

    @patch("src.infrastructure.repositories.gemini_repository.genai.Client")
    def test_parse_empty_name_skipped(self, mock_client_class, mock_gemini_config):
        """空の名前を持つタスクはスキップされる"""
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        response = """```json
{
  "tasks": [
    {"name": "", "task_type": "Must"},
    {"name": "有効なタスク", "task_type": "Must"}
  ]
}
```"""

        repo = GeminiRepository(mock_gemini_config)
        tasks = repo._parse_tasks_from_json(response)

        assert len(tasks) == 1
        assert tasks[0].name == "有効なタスク"

    @patch("src.infrastructure.repositories.gemini_repository.genai.Client")
    def test_parse_all_tasks_have_is_completed_false(
        self, mock_client_class, mock_gemini_config, valid_json_response
    ):
        """全てのタスクのis_completedがFalseであることを確認"""
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        repo = GeminiRepository(mock_gemini_config)
        tasks = repo._parse_tasks_from_json(valid_json_response)

        assert all(task.is_completed is False for task in tasks)


# =============================================================================
# generate_tasks メソッドテスト
# =============================================================================


class TestGenerateTasks:
    """generate_tasks メソッドのテスト"""

    @patch("src.infrastructure.repositories.gemini_repository.genai.Client")
    def test_generate_tasks_success(
        self,
        mock_client_class,
        mock_gemini_config,
        sample_notes,
        sample_events,
        valid_json_response,
    ):
        """タスク生成が成功する場合"""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.text = valid_json_response
        mock_client.models.generate_content.return_value = mock_response
        mock_client_class.return_value = mock_client

        repo = GeminiRepository(mock_gemini_config)
        tasks = repo.generate_tasks(
            arhievment_rate=0.8,
            relevant_notes=sample_notes,
            events=sample_events,
        )

        assert len(tasks) == 4
        mock_client.models.generate_content.assert_called_once()

    @patch("src.infrastructure.repositories.gemini_repository.genai.Client")
    def test_generate_tasks_reads_prompt_file(
        self,
        mock_client_class,
        mock_gemini_config,
        sample_notes,
        sample_events,
        valid_json_response,
    ):
        """プロンプトファイルが読み込まれることを確認"""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.text = valid_json_response
        mock_client.models.generate_content.return_value = mock_response
        mock_client_class.return_value = mock_client

        repo = GeminiRepository(mock_gemini_config)
        repo.generate_tasks(
            arhievment_rate=0.7,
            relevant_notes=sample_notes,
            events=sample_events,
        )

        # generate_contentが呼ばれた際の引数を確認
        call_args = mock_client.models.generate_content.call_args
        prompt = call_args.kwargs.get("contents") or call_args[1].get("contents")
        # プロンプトファイルの内容が含まれていることを確認
        assert "Test Prompt" in prompt

    @patch("src.infrastructure.repositories.gemini_repository.genai.Client")
    def test_generate_tasks_uses_correct_model(
        self,
        mock_client_class,
        mock_gemini_config,
        sample_notes,
        sample_events,
        valid_json_response,
    ):
        """正しいモデルが使用されることを確認"""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.text = valid_json_response
        mock_client.models.generate_content.return_value = mock_response
        mock_client_class.return_value = mock_client

        repo = GeminiRepository(mock_gemini_config)
        repo.generate_tasks(
            arhievment_rate=0.6,
            relevant_notes=sample_notes,
            events=sample_events,
        )

        # generate_contentが正しいモデルで呼ばれたことを確認
        call_args = mock_client.models.generate_content.call_args
        model = call_args.kwargs.get("model") or call_args[1].get("model")
        assert model == "gemini-test-model"

    @patch("src.infrastructure.repositories.gemini_repository.genai.Client")
    def test_generate_tasks_with_empty_response(
        self, mock_client_class, mock_gemini_config, sample_notes, sample_events
    ):
        """空のレスポンスの場合は空リストを返す"""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.text = ""
        mock_client.models.generate_content.return_value = mock_response
        mock_client_class.return_value = mock_client

        repo = GeminiRepository(mock_gemini_config)
        tasks = repo.generate_tasks(
            arhievment_rate=0.5,
            relevant_notes=sample_notes,
            events=sample_events,
        )

        assert tasks == []


# =============================================================================
# 初期化テスト
# =============================================================================


class TestGeminiRepositoryInit:
    """GeminiRepository 初期化のテスト"""

    @patch("src.infrastructure.repositories.gemini_repository.genai.Client")
    def test_init_with_config(self, mock_client_class, mock_gemini_config):
        """設定を指定して初期化"""
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        repo = GeminiRepository(mock_gemini_config)

        assert repo.config == mock_gemini_config
        mock_client_class.assert_called_once_with(api_key="test_api_key")

    @patch("src.infrastructure.repositories.gemini_repository.genai.Client")
    def test_init_creates_client(self, mock_client_class, mock_gemini_config):
        """クライアントが作成されることを確認"""
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        repo = GeminiRepository(mock_gemini_config)

        assert repo.client == mock_client
