from datetime import datetime, timedelta, timezone
from pathlib import Path
from logging import getLogger
from typing import List

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build, Resource
from googleapiclient.errors import HttpError

from src.domain.models.calendar import Calendar, Event
from src.domain.repository.calendar_repository import CalendarRepository
from src.infrastructure.config import GoogleCalendarConfig

logger = getLogger(__name__)


class GoogleCalendarRepository(CalendarRepository):
    """Google Calendar のリポジトリ

    Args:
        config(GoogleCalendarConfig): 設定

    Raises:
        HttpError: エラーが発生した場合
    """

    def __init__(self, config: GoogleCalendarConfig) -> None:
        self.config = config
        self.credentials = None
        self.service = None

        if Path(config.token_path).exists():
            self.credentials = Credentials.from_authorized_user_file(
                config.token_path, config.scopes
            )

        if not self.credentials or not self.credentials.valid:
            if (
                self.credentials
                and self.credentials.expired
                and self.credentials.refresh_token
            ):
                self.credentials.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    config.credentials_path, config.scopes
                )
                self.credentials = flow.run_local_server(port=0)
                with open(config.token_path, "w") as token:
                    token.write(self.credentials.to_json())

        self.service = self._get_valid_service()

    def _get_valid_service(self) -> Resource:
        if (
            self.credentials
            and self.credentials.expired
            and self.credentials.refresh_token
        ):
            self.credentials.refresh(Request())
            # 必要に応じて service を再構築
            self.service = build("calendar", "v3", credentials=self.credentials)
        elif self.service is None and self.credentials:
            # service が未初期化の場合は初期化
            self.service = build("calendar", "v3", credentials=self.credentials)

        if self.service is None:
            raise RuntimeError("Google Calendar service の初期化に失敗しました")
        return self.service

    def get_calendars(self) -> List[Calendar]:
        """カレンダーを取得する
        Returns:
            List[Calendar]: カレンダー
        """
        calendars = []
        try:
            service = self._get_valid_service()
            calendars = service.calendars().list().execute()  # type: ignore[attr-defined]
            return [
                Calendar(name=calendar["summary"])
                for calendar in calendars.get("items", [])
            ]
        except HttpError as error:
            logger.error(f"カレンダーの取得に失敗しました: {error}")
            raise error

    def get_events(
        self,
        start_date: datetime = datetime.now(timezone.utc),
        end_date: datetime = datetime.now(timezone.utc) + timedelta(days=30),
        limit: int = 100,
    ) -> List[Event]:
        """イベントを取得する"""
        try:
            service = self._get_valid_service()
            # ISOフォーマット文字列への変換を推奨
            events_result = (
                service.events()  # type: ignore[attr-defined]
                .list(
                    calendarId=self.config.calendar_id,
                    timeMin=start_date.isoformat(),
                    timeMax=end_date.isoformat(),
                    maxResults=limit,
                    singleEvents=True,  # 繰り返しの予定を個別に展開するために推奨
                    orderBy="startTime",
                )
                .execute()
            )

            items = events_result.get("items", [])
            return [
                Event(
                    name=item.get("summary", "(No Title)"),
                    # 終日予定などの場合、dateTimeではなくdateキーになる点に注意
                    start=item["start"].get("dateTime", item["start"].get("date")),
                    end=item["end"].get("dateTime", item["end"].get("date")),
                    description=item.get("description", ""),
                )
                for item in items
            ]
        except HttpError as error:
            logger.error(f"イベントの取得に失敗しました: {error}")
            raise  # 例外を再送出し、呼び出し元で処理させる（finallyでの戻しは不要）

    def get_event(self, event_id: str) -> Event:
        """イベントを取得する"""
        try:
            service = self._get_valid_service()
            event = (
                service.events()  # type: ignore[attr-defined]
                .get(calendarId=self.config.calendar_id, eventId=event_id)
                .execute()
            )
            return Event(
                name=event.get("summary", ""),
                start=event["start"].get("dateTime", event["start"].get("date")),
                end=event["end"].get("dateTime", event["end"].get("date")),
                description=event.get("description", ""),
            )
        except HttpError as error:
            logger.error(f"イベントの取得に失敗しました (ID: {event_id}): {error}")
            raise
