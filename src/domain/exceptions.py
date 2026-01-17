"""
NoteRepository 関連のカスタム例外クラス
"""


class NoteRepositoryError(Exception):
    """NoteRepository の基底例外クラス"""
    pass


class NoteNotFoundError(NoteRepositoryError):
    """ノートが見つからない場合に発生する例外
    
    Attributes:
        file_name: 見つからなかったファイル名
        message: エラーメッセージ
    """
    def __init__(self, file_name: str, message: str = None):
        self.file_name = file_name
        self.message = message or f"ノートが見つかりません: {file_name}"
        super().__init__(self.message)


class NoteParseError(NoteRepositoryError):
    """ノートのパースに失敗した場合に発生する例外
    
    Attributes:
        file_name: パースに失敗したファイル名
        message: エラーメッセージ
        original_error: 元の例外
    """
    def __init__(self, file_name: str, message: str = None, original_error: Exception = None):
        self.file_name = file_name
        self.original_error = original_error
        self.message = message or f"ノートのパースに失敗しました: {file_name}"
        super().__init__(self.message)


class NoteIOError(NoteRepositoryError):
    """ファイルI/O エラーが発生した場合に発生する例外
    
    Attributes:
        file_path: エラーが発生したファイルパス
        message: エラーメッセージ
        original_error: 元の例外
    """
    def __init__(self, file_path: str, message: str = None, original_error: Exception = None):
        self.file_path = file_path
        self.original_error = original_error
        self.message = message or f"ファイルI/Oエラーが発生しました: {file_path}"
        super().__init__(self.message)


class InvalidVaultPathError(NoteRepositoryError):
    """Vault パスが無効な場合に発生する例外
    
    Attributes:
        vault_path: 無効なVaultパス
        message: エラーメッセージ
    """
    def __init__(self, vault_path: str, message: str = None):
        self.vault_path = vault_path
        self.message = message or f"無効なVaultパスです: {vault_path}"
        super().__init__(self.message)
