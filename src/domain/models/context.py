from dataclasses import dataclass, field
from typing import List

from src.domain.models.note import Note, NoteType
from src.domain.models.calendar import Event


@dataclass
class NoteMetadata:
    """ノートのメタデータ（目次用）

    Attributes:
        name(str): ノートのファイル名
        title(str): ノートのタイトル
        tags(List[str]): タグ一覧
        note_type(NoteType): ノートの種類
        links(List[str]): リンク先一覧
    """

    name: str = field(default="")
    title: str = field(default="")
    tags: List[str] = field(default_factory=list)
    note_type: NoteType = field(default=NoteType.Literature)
    links: List[str] = field(default_factory=list)

    @classmethod
    def from_note(cls, note: Note) -> "NoteMetadata":
        """Note から NoteMetadata を生成する

        Args:
            note(Note): ノート

        Returns:
            NoteMetadata: メタデータ
        """
        return cls(
            name=note.name,
            title=note.properties.title,
            tags=note.properties.tags,
            note_type=note.note_type,
            links=note.links,
        )

    def to_dict(self) -> dict:
        """辞書形式に変換する（Gemini への送信用）

        Returns:
            dict: 辞書形式のメタデータ
        """
        return {
            "name": self.name,
            "title": self.title,
            "tags": self.tags,
            "note_type": self.note_type.name,
            "links": self.links,
        }


@dataclass
class InitialContext:
    """Gemini に渡す初期コンテキスト

    Attributes:
        index_notes(List[Note]): L3: 長期目標（Index ノート）
        weekly_daily_notes(List[Note]): L1: 過去7日分の Daily ノート
        events(List[Event]): カレンダーのイベント一覧
        achievement_rate(float): 昨日の達成率
        note_metadata_list(List[NoteMetadata]): 全ノートのメタデータ（目次）
    """

    index_notes: List[Note] = field(default_factory=list)
    weekly_daily_notes: List[Note] = field(default_factory=list)
    events: List[Event] = field(default_factory=list)
    achievement_rate: float = field(default=0.0)
    note_metadata_list: List[NoteMetadata] = field(default_factory=list)

    def format_for_prompt(self) -> str:
        """プロンプト用にフォーマットする

        Returns:
            str: フォーマットされた文字列
        """
        sections = []

        # 達成率
        sections.append(f"## 昨日の達成率\n{self.achievement_rate:.1%}")

        # Index ノート（長期目標）
        if self.index_notes:
            index_section = "## Index ノート（長期目標）\n"
            for note in self.index_notes:
                index_section += f"### {note.properties.title or note.name}\n"
                index_section += f"{note.content}\n\n"
            sections.append(index_section)

        # 過去7日間の Daily ノート
        if self.weekly_daily_notes:
            daily_section = "## 過去7日間の Daily ノート\n"
            for note in self.weekly_daily_notes:
                daily_section += f"### {note.properties.title or note.name}\n"
                # 最初の500文字のみ（トークン節約）
                content_preview = (
                    note.content[:500] + "..."
                    if len(note.content) > 500
                    else note.content
                )
                daily_section += f"{content_preview}\n\n"
            sections.append(daily_section)

        # カレンダーイベント
        if self.events:
            events_section = "## 今日の予定（カレンダー）\n"
            for event in self.events:
                events_section += f"- {event.name} ({event.start} ~ {event.end})\n"
                if event.description:
                    events_section += f"  説明: {event.description}\n"
            sections.append(events_section)

        # ノートメタデータ一覧（目次）
        if self.note_metadata_list:
            metadata_section = "## ノート一覧（目次）\n"
            metadata_section += "以下のノートが利用可能です。詳細が必要な場合は `read_note` ツールで取得してください。`read_note` ツールを使用する場合は、ファイル名を使用してください。\n\n"
            for meta in self.note_metadata_list:
                metadata_section += f"- **{meta.name}** (type: {meta.note_type.name})\n"
                metadata_section += f"  - ファイル名: {meta.name}\n"
                if meta.title:
                    metadata_section += f"  - タイトル: {meta.title}\n"
                if meta.tags:
                    metadata_section += f"  - タグ: {', '.join(meta.tags)}\n"
            sections.append(metadata_section)

        return "\n\n".join(sections)
