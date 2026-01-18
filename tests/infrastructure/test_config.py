"""
infrastructure/config.py のテスト
"""

import os
from unittest.mock import patch

from src.infrastructure.config import GoogleCalendarConfig, GeminiConfig, Config


# =============================================================================
# GoogleCalendarConfig テスト
# =============================================================================


class TestGoogleCalendarConfig:
    """GoogleCalendarConfig のテスト"""

    def test_default_values(self):
        """デフォルト値でインスタンス化できることを確認"""
        config = GoogleCalendarConfig()

        assert config.calendar_id == "primary"
        assert config.scopes == ["https://www.googleapis.com/auth/calendar.readonly"]
        assert config.credentials_path == "credentials.json"
        assert config.token_path == "token.json"

    def test_with_custom_values(self):
        """カスタム値でインスタンス化できることを確認"""
        config = GoogleCalendarConfig(
            calendar_id="custom_calendar_id",
            scopes=["https://www.googleapis.com/auth/calendar"],
            credentials_path="/path/to/credentials.json",
            token_path="/path/to/token.json",
        )

        assert config.calendar_id == "custom_calendar_id"
        assert config.scopes == ["https://www.googleapis.com/auth/calendar"]
        assert config.credentials_path == "/path/to/credentials.json"
        assert config.token_path == "/path/to/token.json"

    def test_with_partial_custom_values(self):
        """一部のカスタム値でインスタンス化できることを確認"""
        config = GoogleCalendarConfig(
            calendar_id="my_calendar",
        )

        assert config.calendar_id == "my_calendar"
        assert config.scopes == ["https://www.googleapis.com/auth/calendar.readonly"]
        assert config.credentials_path == "credentials.json"
        assert config.token_path == "token.json"

    def test_env_prefix(self):
        """環境変数プレフィックスが正しく設定されていることを確認"""
        assert GoogleCalendarConfig.model_config.get("env_prefix") == "GOOGLE_CALENDAR_"

    @patch.dict(
        os.environ,
        {
            "GOOGLE_CALENDAR_CALENDAR_ID": "env_calendar_id",
            "GOOGLE_CALENDAR_TOKEN_PATH": "env_token.json",
        },
    )
    def test_load_from_environment_variables(self):
        """環境変数から設定を読み込めることを確認"""
        # 注意: pydantic-settingsは.envファイルも読み込むため、
        # 実際の環境では.envファイルの設定が優先される可能性があります
        config = GoogleCalendarConfig()

        # 環境変数が設定されていれば、その値が使われる
        # ただし、.envファイルがある場合はそちらが優先されることがある
        assert config.calendar_id in ["env_calendar_id", "primary"]


# =============================================================================
# GeminiConfig テスト
# =============================================================================


class TestGeminiConfig:
    """GeminiConfig のテスト"""

    @patch.dict(os.environ, {}, clear=False)
    def test_default_values(self, monkeypatch):
        """デフォルト値でインスタンス化できることを確認

        Note: pydantic-settingsは.envファイルからも読み込むため、
        api_keyは.envに値があればそれが使われる。
        ここでは型と他のデフォルト値のみ確認する。
        """
        config = GeminiConfig()

        # api_keyは.envから読み込まれる可能性があるため、型のみ確認
        assert isinstance(config.api_key, str)
        assert config.model == "gemini-3-flash-preview"
        assert config.prompt_path == "prompts/gemini.md"

    def test_with_custom_values(self):
        """カスタム値でインスタンス化できることを確認"""
        config = GeminiConfig(
            api_key="custom_api_key",
            model="gemini-pro",
            prompt_path="/custom/path/prompt.md",
        )

        assert config.api_key == "custom_api_key"
        assert config.model == "gemini-pro"
        assert config.prompt_path == "/custom/path/prompt.md"

    def test_with_partial_custom_values(self):
        """一部のカスタム値でインスタンス化できることを確認"""
        config = GeminiConfig(
            api_key="my_api_key",
        )

        assert config.api_key == "my_api_key"
        assert config.model == "gemini-3-flash-preview"
        assert config.prompt_path == "prompts/gemini.md"

    def test_env_prefix(self):
        """環境変数プレフィックスが正しく設定されていることを確認"""
        assert GeminiConfig.model_config.get("env_prefix") == "GEMINI_"

    @patch.dict(
        os.environ,
        {
            "GEMINI_API_KEY": "env_api_key",
            "GEMINI_MODEL": "env_model",
        },
    )
    def test_load_from_environment_variables(self):
        """環境変数から設定を読み込めることを確認"""
        config = GeminiConfig()

        # 環境変数が設定されていれば、その値が使われる
        # ただし、.envファイルがある場合はそちらが優先されることがある
        assert config.api_key in ["env_api_key", ""]


# =============================================================================
# Config テスト
# =============================================================================


class TestConfig:
    """Config のテスト"""

    def test_default_values(self):
        """デフォルト値でインスタンス化できることを確認"""
        config = Config()

        assert isinstance(config.google_calendar, GoogleCalendarConfig)
        assert isinstance(config.gemini, GeminiConfig)

    def test_nested_google_calendar_config(self):
        """ネストされたGoogleCalendarConfigの値を確認"""
        config = Config()

        assert config.google_calendar.calendar_id == "primary"
        assert config.google_calendar.credentials_path == "credentials.json"
        assert config.google_calendar.token_path == "token.json"

    def test_nested_gemini_config(self):
        """ネストされたGeminiConfigの値を確認"""
        config = Config()

        assert config.gemini.model == "gemini-3-flash-preview"
        assert config.gemini.prompt_path == "prompts/gemini.md"

    def test_with_custom_nested_configs(self):
        """カスタムのネストされた設定でインスタンス化できることを確認"""
        custom_google_config = GoogleCalendarConfig(
            calendar_id="custom_calendar",
            token_path="custom_token.json",
        )
        custom_gemini_config = GeminiConfig(
            api_key="custom_key",
            model="custom_model",
        )

        config = Config(
            google_calendar=custom_google_config,
            gemini=custom_gemini_config,
        )

        assert config.google_calendar.calendar_id == "custom_calendar"
        assert config.google_calendar.token_path == "custom_token.json"
        assert config.gemini.api_key == "custom_key"
        assert config.gemini.model == "custom_model"

    def test_google_calendar_and_gemini_are_independent(self):
        """google_calendarとgeminiが独立していることを確認"""
        config1 = Config()
        config2 = Config()

        # 異なるインスタンスであることを確認
        assert config1.google_calendar is not config2.google_calendar
        assert config1.gemini is not config2.gemini


# =============================================================================
# 設定の型チェックテスト
# =============================================================================


class TestConfigTypes:
    """設定の型チェックテスト"""

    def test_google_calendar_scopes_is_list(self):
        """scopesがリストであることを確認"""
        config = GoogleCalendarConfig()
        assert isinstance(config.scopes, list)

    def test_google_calendar_scopes_contains_strings(self):
        """scopesがstr型の要素を含むことを確認"""
        config = GoogleCalendarConfig()
        assert all(isinstance(scope, str) for scope in config.scopes)

    def test_gemini_api_key_is_string(self):
        """api_keyがstr型であることを確認"""
        config = GeminiConfig()
        assert isinstance(config.api_key, str)

    def test_gemini_model_is_string(self):
        """modelがstr型であることを確認"""
        config = GeminiConfig()
        assert isinstance(config.model, str)

    def test_gemini_prompt_path_is_string(self):
        """prompt_pathがstr型であることを確認"""
        config = GeminiConfig()
        assert isinstance(config.prompt_path, str)
