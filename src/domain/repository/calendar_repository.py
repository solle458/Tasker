from abc import ABC, abstractmethod
from typing import List
from datetime import datetime

from src.domain.models.calendar import Calendar, Event


class CalendarRepository(ABC):
    @abstractmethod
    def get_calendars(self) -> List[Calendar]:
        """カレンダーを取得する
        Returns:
            List[Calendar]: カレンダー
        """
        pass

    @abstractmethod
    def get_events(
        self, start_date: datetime, end_date: datetime, limit: int
    ) -> List[Event]:
        """イベントを取得する
        Args:
            start_date(datetime): 開始日
            end_date(datetime): 終了日
            limit(int): 取得件数
        Returns:
            List[Event]: イベント
        """
        pass

    @abstractmethod
    def get_event(self, event_id: str) -> Event:
        """イベントを取得する
        Args:
            event_id(str): イベントID
        Returns:
            Event: イベント
        """
        pass
