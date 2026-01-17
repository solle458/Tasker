import re
import yaml
import frontmatter
from typing import List, Optional
from pathlib import Path
from datetime import datetime


from domain.repository.note_repository import NoteRepository
from src.domain.models.note import Note, NoteType, Property

class ObsidianRepository(NoteRepository):
    """
    Obsidian のノートを管理するリポジトリ
    Args:
        obsidian_path(str): Obsidian のパス
    """

    def __init__(self, obsidian_path: str):
        self.obsidian_path = Path(obsidian_path)

    def _read_file(self, file_name: str) -> str:
        """ファイルを読み込む
        Args:
            file_name(str): ファイル名

        Returns:
            str: ファイルの内容
        """
        note_path = self.obsidian_path / file_name
        with open(note_path, 'r') as file:
            return file.read()
    
    def _parse_frontmatter(self, file_name: str) -> Property:
        """Frontmatter をパースする
        Args:
            file_name(str): ファイル名

        Returns:
            Property: プロパティ
        """
        frontmatter_data = frontmatter.load(Path(self.obsidian_path / file_name))
        return Property(
            tags=frontmatter_data.get('tags', []),
            title=frontmatter_data.get('title', ''),
            aliases=frontmatter_data.get('aliases', []),
            uid=frontmatter_data.get('uid', ''),
        )

    def _extract_links(self, raw_content: str) -> List[str]:
        """本文からWikiリンク（[[link]]）を抽出する。

        Args:
            raw_content(str): 本文

        Returns:
            List[str]: 抽出されたリンク先のリスト。
        """
        links = r'\[\[([^\]|]+)(?:\|[^\]]+)?\]\]'
        return list(set(re.findall(links, raw_content)))

    def _determine_note_type(self, tags: List[str]) -> NoteType:
        """タグからノートの種類を決定する
        Args:
            tags(List[str]): タグ

        Returns:
            NoteType: ノートの種類
        """
        if 'obsidian/section/index' in tags:
            return NoteType.Index
        elif 'obsidian/section/structure' in tags:
            return NoteType.Structure
        elif 'obsidian/section/daily' in tags:
            return NoteType.Daily
        elif 'obsidian/section/literature' in tags:
            return NoteType.Literature
        elif 'obsidian/section/fleeting' in tags:
            return NoteType.Fleeting
        elif 'obsidian/section/permanent' in tags:
            return NoteType.Permanent
        else:
            return NoteType.Literature

    def get_all_note_names(self) -> List[str]:
        """すべてのノートのファイル名を取得する
        Returns:
            List[str]: ノートのファイル名
        """
        return [file.name for file in self.obsidian_path.glob('*.md')]

    def get_all_notes(self) -> List[Note]:
        """すべてのノートを取得する
        Returns:
            List[Note]: ノート
        """
        return [self.get_by_file_name(file_name) for file_name in self.get_all_note_names()]

    def get_by_file_name(self, file_name: str) -> Optional[Note]:
        """ファイル名でノートを取得する
        Args:
            file_name(str): ファイル名

        Returns:
            Optional[Note]: ノート
        """

        # ファイル読み込み
        raw_content = self._read_file(file_name)
        # メタデータ, リンク, 本文のパース
        properties = self._parse_frontmatter(file_name)
        links = self._extract_links(raw_content)
        content = raw_content.split('---', 2)[2].strip()
        # ノートの種類を決定
        note_type = self._determine_note_type(properties.tags)
        # ノートを返す
        return Note(
            name=file_name,
            properties=properties,
            content=content,
            links=links,
            note_type=note_type,
        )

    def find_by_tag(self, tag: str) -> List[Note]:
        """タグでノートを取得する
        Args:
            tag(str): タグ

        Returns:
            List[Note]: ノート
        """
        return [note for note in self.get_all_notes() if tag in note.properties.tags]

    def find_by_note_type(self, note_type: NoteType) -> List[Note]:
        """ノートの種類でノートを取得する
        Args:
            note_type(NoteType): ノートの種類

        Returns:
            List[Note]: ノート
        """
        return [note for note in self.get_all_notes() if note.note_type == note_type]

    def get_links(self, note: Note) -> List[Note]:
        """ノートのリンクを取得する
        Args:
            note(Note): ノート

        Returns:
            List[Note]: リンク先のノート
        """
        return [self.get_by_file_name(link) for link in note.links]
    
    def search_by_text(self, query: str) -> List[Note]:
        """タイトルや本文から全文検索を行う
        Args:
            query(str): 検索クエリ

        Returns:
            List[Note]: ノート
        """
        return [note for note in self.get_all_notes() if query in note.content or query in note.properties.title]

    def get_daily_notes(self, days: int) -> List[Note]:
        """日記を取得する
        Args:
            days(int): 日数

        Returns:
            List[Note]: 日記
        """
        daily_notes = [note for note in self.get_all_notes() if note.note_type == NoteType.Daily]
        return daily_notes[-days:]

    def save_daily_note(self, note: Note) -> None:
        """日記を保存する
        Args:
            note(Note): 日記
        """
        daily_note_path = self.obsidian_path / datetime.now().strftime("%Y-%m-%dT-%H-%M-%S.md")

        # Propertyを辞書形式に変換
        property_dict = {
            'tags': note.properties.tags,
            'title': note.properties.title,
            'aliases': note.properties.aliases,
            'uid': note.properties.uid,
        }

        # YAML文字列に変換
        yaml_frontmatter = yaml.dump(property_dict, allow_unicode=True, default_flow_style=False)
        # markdown形式に変換
        markdown_content = f"---\n{yaml_frontmatter}\n---\n{note.content}"
        with open(daily_note_path, 'w') as file:
            file.write(markdown_content)