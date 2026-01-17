import re
import yaml
import logging
import frontmatter
from typing import List, Optional, Dict
from pathlib import Path
from datetime import datetime


from domain.repository.note_repository import NoteRepository
from src.domain.models.note import Note, NoteType, Property
from src.domain.exceptions import (
    NoteNotFoundError,
    NoteParseError,
    NoteIOError,
    InvalidVaultPathError,
)

# モジュールレベルのロガー
logger = logging.getLogger(__name__)


class ObsidianRepository(NoteRepository):
    """
    Obsidian のノートを管理するリポジトリ
    
    Args:
        obsidian_path(str): Obsidian のパス
        
    Raises:
        InvalidVaultPathError: 指定されたパスが存在しない、またはディレクトリでない場合
    """

    def __init__(self, obsidian_path: str):
        self.obsidian_path = Path(obsidian_path)
        
        # パスの存在確認
        if not self.obsidian_path.exists():
            logger.error(f"Vaultパスが存在しません: {obsidian_path}")
            raise InvalidVaultPathError(
                obsidian_path, 
                f"指定されたパスが存在しません: {obsidian_path}"
            )
        
        if not self.obsidian_path.is_dir():
            logger.error(f"Vaultパスがディレクトリではありません: {obsidian_path}")
            raise InvalidVaultPathError(
                obsidian_path,
                f"指定されたパスはディレクトリではありません: {obsidian_path}"
            )
        
        # キャッシュの初期化
        self._cache: Dict[str, Note] = {}
        self._cache_loaded: bool = False
        
        logger.info(f"ObsidianRepository を初期化しました: {obsidian_path}")

    def _read_file(self, file_name: str) -> str:
        """ファイルを読み込む
        
        Args:
            file_name(str): ファイル名

        Returns:
            str: ファイルの内容
            
        Raises:
            NoteIOError: ファイルの読み込みに失敗した場合
        """
        note_path = self.obsidian_path / file_name
        
        try:
            with open(note_path, 'r', encoding='utf-8') as file:
                content = file.read()
                logger.debug(f"ファイルを読み込みました: {file_name}")
                return content
        except FileNotFoundError as e:
            logger.error(f"ファイルが見つかりません: {note_path}")
            raise NoteNotFoundError(file_name, f"ファイルが見つかりません: {note_path}")
        except PermissionError as e:
            logger.error(f"ファイルの読み込み権限がありません: {note_path}")
            raise NoteIOError(
                str(note_path),
                f"ファイルの読み込み権限がありません: {note_path}",
                e
            )
        except UnicodeDecodeError as e:
            logger.error(f"ファイルのエンコーディングエラー: {note_path}")
            raise NoteIOError(
                str(note_path),
                f"ファイルのエンコーディングエラー（UTF-8でない可能性があります）: {note_path}",
                e
            )
        except OSError as e:
            logger.error(f"ファイルI/Oエラー: {note_path} - {e}")
            raise NoteIOError(str(note_path), f"ファイルI/Oエラー: {note_path}", e)

    def _parse_frontmatter_from_content(self, file_name: str, raw_content: str) -> Property:
        """コンテンツからFrontmatter をパースする
        
        Args:
            file_name(str): ファイル名（エラーメッセージ用）
            raw_content(str): ファイルの生の内容

        Returns:
            Property: プロパティ
            
        Raises:
            NoteParseError: Frontmatterのパースに失敗した場合
        """
        try:
            parsed = frontmatter.loads(raw_content)
            return Property(
                tags=parsed.get('tags', []) or [],
                title=parsed.get('title', '') or '',
                aliases=parsed.get('aliases', []) or [],
                uid=parsed.get('uid', '') or '',
            )
        except yaml.YAMLError as e:
            logger.error(f"Frontmatterのパースに失敗しました: {file_name} - {e}")
            raise NoteParseError(
                file_name,
                f"Frontmatter（YAML）のパースに失敗しました: {file_name}",
                e
            )
        except Exception as e:
            logger.error(f"Frontmatterのパース中に予期しないエラー: {file_name} - {e}")
            raise NoteParseError(
                file_name,
                f"Frontmatterのパース中に予期しないエラーが発生しました: {file_name}",
                e
            )

    def _extract_content_body(self, file_name: str, raw_content: str) -> str:
        """Frontmatterを除いた本文を抽出する
        
        Args:
            file_name(str): ファイル名（エラーメッセージ用）
            raw_content(str): ファイルの生の内容

        Returns:
            str: 本文
            
        Raises:
            NoteParseError: 本文の抽出に失敗した場合
        """
        try:
            # Frontmatterがない場合はそのまま返す
            if not raw_content.startswith('---'):
                return raw_content.strip()
            
            parts = raw_content.split('---', 2)
            if len(parts) >= 3:
                return parts[2].strip()
            else:
                # Frontmatterの終了区切りがない場合
                logger.warning(f"Frontmatterの形式が不正です（終了区切りなし）: {file_name}")
                return raw_content.strip()
        except Exception as e:
            logger.error(f"本文の抽出に失敗しました: {file_name} - {e}")
            raise NoteParseError(
                file_name,
                f"本文の抽出に失敗しました: {file_name}",
                e
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
        tag_to_type = {
            'obsidian/section/index': NoteType.Index,
            'obsidian/section/structure': NoteType.Structure,
            'obsidian/section/daily': NoteType.Daily,
            'obsidian/section/literature': NoteType.Literature,
            'obsidian/section/fleeting': NoteType.Fleeting,
            'obsidian/section/permanent': NoteType.Permanent,
        }
        
        for tag, note_type in tag_to_type.items():
            if tag in tags:
                return note_type
        
        return NoteType.Literature

    def refresh_cache(self) -> None:
        """キャッシュを明示的にリフレッシュする
        
        全ノートを再読み込みしてキャッシュを更新します。
        """
        logger.info("キャッシュをリフレッシュします")
        self._cache.clear()
        self._cache_loaded = False
        
        # 全ノートを読み込んでキャッシュ
        for file_name in self.get_all_note_names():
            try:
                self._load_note_to_cache(file_name)
            except Exception as e:
                logger.warning(f"キャッシュリフレッシュ中にエラー（スキップ）: {file_name} - {e}")
        
        self._cache_loaded = True
        logger.info(f"キャッシュリフレッシュ完了: {len(self._cache)}件")

    def clear_cache(self) -> None:
        """キャッシュをクリアする"""
        self._cache.clear()
        self._cache_loaded = False
        logger.info("キャッシュをクリアしました")

    def _load_note_to_cache(self, file_name: str) -> Note:
        """ノートを読み込んでキャッシュに保存する
        
        Args:
            file_name(str): ファイル名

        Returns:
            Note: 読み込んだノート
            
        Raises:
            NoteNotFoundError: ファイルが見つからない場合
            NoteIOError: ファイルの読み込みに失敗した場合
            NoteParseError: ノートのパースに失敗した場合
        """
        # ファイル読み込み（1回だけ）
        raw_content = self._read_file(file_name)
        
        # メタデータのパース
        properties = self._parse_frontmatter_from_content(file_name, raw_content)
        
        # リンク抽出
        links = self._extract_links(raw_content)
        
        # 本文抽出
        content = self._extract_content_body(file_name, raw_content)
        
        # ノートの種類を決定
        note_type = self._determine_note_type(properties.tags)
        
        # ノートを生成
        note = Note(
            name=file_name,
            properties=properties,
            content=content,
            links=links,
            note_type=note_type,
        )
        
        # キャッシュに保存
        self._cache[file_name] = note
        logger.debug(f"ノートをキャッシュに保存: {file_name}")
        
        return note

    def get_all_note_names(self) -> List[str]:
        """すべてのノートのファイル名を取得する
        
        Returns:
            List[str]: ノートのファイル名
        """
        try:
            names = [file.name for file in self.obsidian_path.glob('*.md')]
            logger.debug(f"ノート一覧を取得: {len(names)}件")
            return names
        except OSError as e:
            logger.error(f"ノート一覧の取得に失敗: {e}")
            raise NoteIOError(
                str(self.obsidian_path),
                f"ノート一覧の取得に失敗しました: {self.obsidian_path}",
                e
            )

    def get_all_notes(self) -> List[Note]:
        """すべてのノートを取得する
        
        キャッシュが有効な場合はキャッシュから返却します。
        
        Returns:
            List[Note]: ノート
        """
        # キャッシュが有効な場合
        if self._cache_loaded:
            logger.debug("キャッシュから全ノートを返却")
            return list(self._cache.values())
        
        # キャッシュを構築
        notes = []
        for file_name in self.get_all_note_names():
            try:
                note = self.get_by_file_name(file_name)
                if note:
                    notes.append(note)
            except Exception as e:
                logger.warning(f"ノートの読み込みをスキップ: {file_name} - {e}")
        
        self._cache_loaded = True
        logger.info(f"全ノートを読み込みました: {len(notes)}件")
        return notes

    def get_by_file_name(self, file_name: str) -> Optional[Note]:
        """ファイル名でノートを取得する
        
        キャッシュに存在する場合はキャッシュから返却します。
        
        Args:
            file_name(str): ファイル名

        Returns:
            Optional[Note]: ノート
            
        Raises:
            NoteNotFoundError: ファイルが見つからない場合
            NoteIOError: ファイルの読み込みに失敗した場合
            NoteParseError: ノートのパースに失敗した場合
        """
        # キャッシュにある場合はキャッシュから返却
        if file_name in self._cache:
            logger.debug(f"キャッシュヒット: {file_name}")
            return self._cache[file_name]
        
        logger.debug(f"キャッシュミス、ファイルを読み込みます: {file_name}")
        return self._load_note_to_cache(file_name)

    def find_by_tag(self, tag: str) -> List[Note]:
        """タグでノートを取得する
        
        Args:
            tag(str): タグ

        Returns:
            List[Note]: ノート
        """
        logger.debug(f"タグで検索: {tag}")
        return [note for note in self.get_all_notes() if tag in note.properties.tags]

    def find_by_note_type(self, note_type: NoteType) -> List[Note]:
        """ノートの種類でノートを取得する
        
        Args:
            note_type(NoteType): ノートの種類

        Returns:
            List[Note]: ノート
        """
        logger.debug(f"ノート種類で検索: {note_type}")
        return [note for note in self.get_all_notes() if note.note_type == note_type]

    def get_links(self, note: Note) -> List[Note]:
        """ノートのリンクを取得する
        
        存在しないリンク先はスキップされます。
        
        Args:
            note(Note): ノート

        Returns:
            List[Note]: リンク先のノート
        """
        linked_notes = []
        for link in note.links:
            # リンクにはファイル拡張子がない場合があるため、.md を付与
            file_name = link if link.endswith('.md') else f"{link}.md"
            try:
                linked_note = self.get_by_file_name(file_name)
                if linked_note:
                    linked_notes.append(linked_note)
            except NoteNotFoundError:
                logger.debug(f"リンク先が見つかりません（スキップ）: {link}")
            except Exception as e:
                logger.warning(f"リンク先の読み込みに失敗（スキップ）: {link} - {e}")
        
        return linked_notes
    
    def search_by_text(self, query: str) -> List[Note]:
        """タイトルや本文から全文検索を行う
        
        Args:
            query(str): 検索クエリ

        Returns:
            List[Note]: ノート
        """
        logger.debug(f"テキスト検索: {query}")
        return [
            note for note in self.get_all_notes() 
            if query in note.content or query in note.properties.title
        ]

    def get_daily_notes(self, days: int) -> List[Note]:
        """日記を取得する
        
        Args:
            days(int): 日数

        Returns:
            List[Note]: 日記
        """
        daily_notes = [note for note in self.get_all_notes() if note.note_type == NoteType.Daily]
        logger.debug(f"日記を取得: 全{len(daily_notes)}件中、直近{days}件")
        return daily_notes[-days:]

    def save_daily_note(self, note: Note) -> None:
        """日記を保存する
        
        Args:
            note(Note): 日記
            
        Raises:
            NoteIOError: ファイルの書き込みに失敗した場合
        """
        daily_note_path = self.obsidian_path / datetime.now().strftime("%Y-%m-%dT-%H-%M-%S.md")

        # Propertyを辞書形式に変換
        property_dict = {
            'tags': note.properties.tags,
            'title': note.properties.title,
            'aliases': note.properties.aliases,
            'uid': note.properties.uid,
        }

        try:
            # YAML文字列に変換
            yaml_frontmatter = yaml.dump(property_dict, allow_unicode=True, default_flow_style=False)
            # markdown形式に変換
            markdown_content = f"---\n{yaml_frontmatter}---\n{note.content}"
            
            with open(daily_note_path, 'w', encoding='utf-8') as file:
                file.write(markdown_content)
            
            # キャッシュに追加
            saved_note = Note(
                name=daily_note_path.name,
                properties=note.properties,
                content=note.content,
                links=note.links,
                note_type=note.note_type,
            )
            self._cache[daily_note_path.name] = saved_note
            
            logger.info(f"日記を保存しました: {daily_note_path}")
            
        except PermissionError as e:
            logger.error(f"ファイルの書き込み権限がありません: {daily_note_path}")
            raise NoteIOError(
                str(daily_note_path),
                f"ファイルの書き込み権限がありません: {daily_note_path}",
                e
            )
        except OSError as e:
            logger.error(f"ファイルの書き込みに失敗しました: {daily_note_path} - {e}")
            raise NoteIOError(
                str(daily_note_path),
                f"ファイルの書き込みに失敗しました: {daily_note_path}",
                e
            )
