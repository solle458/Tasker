from dataclasses import dataclass, field
from datetime import datetime
from typing import List
from enum import Enum, auto


class NoteType(Enum):
    """Note type enum
    Attributes:
        Index(str): インデックス(L3)
        Structure(str): 構造(L2)
        Daily(str): 日報(L1)
        Literature(str): 文献
        Fleeting(str): 一時的なノート
        Permanent(str): 永続的なノート
    """

    Index = auto()
    Structure = auto()
    Daily = auto()
    Literature = auto()
    Fleeting = auto()
    Permanent = auto()


@dataclass
class Property:
    """Property entity
    Attributes:
        tags(List[str]): タグ
        title(str): タイトル
        aliases(List[str]): エイリアス
        uid(str): UID
    """

    tags: List[str] = field(default_factory=list)
    title: str = field(default="")
    aliases: List[str] = field(default_factory=list)
    uid: str = field(default="")


@dataclass
class Note:
    """Note entity
    Attributes:
        name(str): ノートの名前
        properties(Property): ノートのプロパティ(tags, title, etc.)
        content(str): ノートの内容
        links(List[str]): リンク
        note_type(NoteType): ノートの種類
    """

    name: str = field(
        default_factory=lambda: datetime.now().strftime("%Y-%m-%d-T%H-%M-%S.md")
    )
    properties: Property = field(default_factory=Property)
    content: str = field(default="")
    links: List[str] = field(default_factory=list)
    note_type: NoteType = field(default=NoteType.Literature)
