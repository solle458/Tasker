from dataclasses import dataclass, field
from typing import List
from datetime import datetime

@dataclass
class Event:
    """Event entity
    Attributes:
        name(str): イベントの名前
        start(datetime): イベントの開始時間
        end(datetime): イベントの終了時間
        description(str): イベントの説明
    """
    name: str = field(default="")
    start: datetime = field(default_factory=datetime.now)
    end: datetime = field(default_factory=datetime.now)
    description: str = field(default="")

@dataclass
class Calendar:
    """Calendar entity
    Attributes:
        name(str): カレンダーの名前
        events(List[Event]): カレンダーのイベント
    """
    name: str = field(default="")
    events: List[Event] = field(default_factory=list)