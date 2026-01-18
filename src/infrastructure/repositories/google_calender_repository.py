from datetime import datetime, timedelta, timezone
from pathlib import Path
from logging import getLogger
from typing import List

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
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

    def _get_valid_service(self) -> build:
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
        return self.service

    def get_calendars(self) -> List[Calendar]:
        """カレンダーを取得する
        Returns:
            List[Calendar]: カレンダー
        """
        calendars = []
        try:
            service = self._get_valid_service()
            calendars = service.calendars().list().execute()
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
        """イベントを取得する
        Args:
            start_date(datetime): 開始日
            end_date(datetime): 終了日
            limit(int): 取得件数
        Returns:
            List[Event]: イベント
        """
        events = []
        try:
            service = self._get_valid_service()
            events = (
                service.events()
                .list(
                    calendarId=self.config.calendar_id,
                    timeMin=start_date,
                    timeMax=end_date,
                    maxResults=limit,
                )
                .execute()
            )
            return [
                Event(
                    name=event["summary"],
                    start=event["start"]["dateTime"],
                    end=event["end"]["dateTime"],
                    description=event["description"],
                )
                for event in events.get("items", [])
            ]
        except HttpError as error:
            logger.error(f"イベントの取得に失敗しました: {error}")
            raise error
        finally:
            return events

    def get_event(self, event_id: str) -> Event:
        """イベントを取得する
        Args:
            event_id(str): イベントID
        Returns:
            Event: イベント
        """
        event = None
        try:
            service = self._get_valid_service()
            event = (
                service.events()
                .get(calendarId=self.config.calendar_id, eventId=event_id)
                .execute()
            )
            return Event(
                name=event["summary"],
                start=event["start"]["dateTime"],
                end=event["end"]["dateTime"],
                description=event["description"],
            )
        except HttpError as error:
            logger.error(f"イベントの取得に失敗しました: {error}")
            raise error
        finally:
            return event
