from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class GoogleCalendarConfig(BaseSettings):
    calendar_id: str = Field(default="primary")
    scopes: list[str] = Field(
        default=["https://www.googleapis.com/auth/calendar.readonly"]
    )
    credentials_path: str = Field(default="credentials.json")
    token_path: str = Field(default="token.json")
    # pydantic-settingsの設定
    model_config = SettingsConfigDict(
        env_prefix="GOOGLE_CALENDAR_",  # 環境変数 GOOGLE_CALENDAR_TOKEN_PATH などに対応
        env_file=".env",
        extra="ignore",
    )


class GeminiConfig(BaseSettings):
    api_key: str = Field(default="")
    model: str = Field(default="gemini-3-flash-preview")
    prompt_path: str = Field(default="prompts/gemini.md")
    model_config = SettingsConfigDict(
        env_prefix="GEMINI_",
        env_file=".env",
        extra="ignore",
    )


class Config(BaseSettings):
    google_calendar: GoogleCalendarConfig = Field(default=GoogleCalendarConfig())
    gemini: GeminiConfig = Field(default=GeminiConfig())
