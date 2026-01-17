from abc import ABC, abstractmethod
from typing import List, Optional

from src.domain.models.note import Note, NoteType

class NoteRepository(ABC):
    @abstractmethod
    def get_by_title(self, title: str) -> Optional[Note]:
        """タイトルでノートを取得する

        Args:
            title(str): タイトル

        Returns:
            Optional[Note]: ノート
        """
        pass

    @abstractmethod
    def find_by_tag(self, tag: str) -> List[Note]:
        """タグでノートを取得する

        Args:
            tag(str): タグ

        Returns:
            List[Note]: ノート
        """
        pass

    @abstractmethod
    def find_by_note_type(self, note_type: NoteType) -> List[Note]:
        """ノートの種類でノートを取得する

        Args:
            note_type(NoteType): ノートの種類

        Returns:
            List[Note]: ノート
        """
        pass

    @abstractmethod
    def get_links(self, note: Note) -> List[str]:
        """ノートのリンクを取得する

        Args:
            note(Note): ノート

        Returns:
            List[str]: リンク
        """
        pass

    @abstractmethod
    def search_by_text(self, query: str) -> List[Note]:
        """タイトルや本文から全文検索を行う (RAG的なアプローチへの備え)

        Args:
            query(str): 検索クエリ

        Returns:
            List[Note]: ノート
        """
        pass

    @abstractmethod
    def get_daily_notes(self, days: int) -> List[Note]:
        """日報を取得する

        Args:
            days(int): 日数

        Returns:
            List[Note]: 日報
        """
        pass

    @abstractmethod
    def save_daily_note(self, note: Note) -> None:
        """生成されたTODOを Daily Note に書き込む

        Args:
            note(Note): 日報
        """
        pass