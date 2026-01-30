import json
import logging
import re
from google import genai
from google.genai import types
from typing import List, Any, Dict

from src.domain.models.task import Task, TaskType
from src.domain.models.note import NoteType
from src.domain.models.context import InitialContext, NoteMetadata
from src.domain.repository.reasoning_repository import ReasoningRepository
from src.domain.repository.note_repository import NoteRepository
from src.infrastructure.config import GeminiConfig

logger = logging.getLogger(__name__)


class GeminiRepository(ReasoningRepository):
    """Gemini のリポジトリ（ReAct Agent 実装）

    Function Calling を使って自律的にノートを探索し、タスクを生成する。

    Args:
        config(GeminiConfig): 設定
        note_repository(NoteRepository): ノートリポジトリ（ツール実行用）
    """

    def __init__(self, config: GeminiConfig, note_repository: NoteRepository) -> None:
        self.config = config
        self.note_repository = note_repository
        self.client = genai.Client(api_key=self.config.api_key)

    # =========================================================================
    # ツール定義
    # =========================================================================

    def _get_tool_declarations(self) -> List[types.FunctionDeclaration]:
        """Function Calling 用のツール宣言を取得する

        Returns:
            List[types.FunctionDeclaration]: ツール宣言のリスト
        """
        return [
            types.FunctionDeclaration(
                name="read_note",
                description="指定したノートの内容を取得する。ノートの詳細な内容が必要な場合に使用する。",
                parameters=types.Schema(
                    type=types.Type.OBJECT,
                    properties={
                        "note_name": types.Schema(
                            type=types.Type.STRING,
                            description="ノートのファイル名（例: 'Project-Aivy.md'）",
                        )
                    },
                    required=["note_name"],
                ),
            ),
            types.FunctionDeclaration(
                name="find_notes_by_tag",
                description="指定したタグを持つノートを検索する。メタデータのみを返す。",
                parameters=types.Schema(
                    type=types.Type.OBJECT,
                    properties={
                        "tag": types.Schema(
                            type=types.Type.STRING,
                            description="検索するタグ（例: 'project/aivy', 'obsidian/section/structure'）",
                        )
                    },
                    required=["tag"],
                ),
            ),
            types.FunctionDeclaration(
                name="find_notes_by_type",
                description="指定したノートタイプのノートを検索する。メタデータのみを返す。",
                parameters=types.Schema(
                    type=types.Type.OBJECT,
                    properties={
                        "note_type": types.Schema(
                            type=types.Type.STRING,
                            description="ノートの種類（Index, Structure, Daily, Literature, Fleeting, Permanent のいずれか）",
                            enum=[
                                "Index",
                                "Structure",
                                "Daily",
                                "Literature",
                                "Fleeting",
                                "Permanent",
                            ],
                        )
                    },
                    required=["note_type"],
                ),
            ),
            types.FunctionDeclaration(
                name="get_note_links",
                description="指定したノートのリンク先一覧を取得する。階層的な探索に使用する。",
                parameters=types.Schema(
                    type=types.Type.OBJECT,
                    properties={
                        "note_name": types.Schema(
                            type=types.Type.STRING,
                            description="ノートのファイル名（例: 'Index-Projects.md'）",
                        )
                    },
                    required=["note_name"],
                ),
            ),
            types.FunctionDeclaration(
                name="search_notes",
                description="タイトルや本文からノートを全文検索する。メタデータのみを返す。",
                parameters=types.Schema(
                    type=types.Type.OBJECT,
                    properties={
                        "query": types.Schema(
                            type=types.Type.STRING,
                            description="検索クエリ（例: 'Aivy', 'バックエンド'）",
                        )
                    },
                    required=["query"],
                ),
            ),
        ]

    # =========================================================================
    # ツール実行
    # =========================================================================

    def _execute_tool(self, name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """ツールを実行する

        Args:
            name(str): ツール名
            args(Dict[str, Any]): ツールの引数

        Returns:
            Dict[str, Any]: ツールの実行結果
        """
        logger.debug(f"ツール実行: {name}({args})")

        try:
            if name == "read_note":
                return self._tool_read_note(args.get("note_name", ""))
            elif name == "find_notes_by_tag":
                return self._tool_find_notes_by_tag(args.get("tag", ""))
            elif name == "find_notes_by_type":
                return self._tool_find_notes_by_type(args.get("note_type", ""))
            elif name == "get_note_links":
                return self._tool_get_note_links(args.get("note_name", ""))
            elif name == "search_notes":
                return self._tool_search_notes(args.get("query", ""))
            else:
                return {"error": f"Unknown tool: {name}"}
        except Exception as e:
            logger.error(f"ツール実行エラー: {name} - {e}")
            return {"error": str(e)}

    def _tool_read_note(self, note_name: str) -> Dict[str, Any]:
        """ノートの内容を取得する"""
        note = self.note_repository.get_by_file_name(note_name)
        if note is None:
            return {"error": f"ノートが見つかりません: {note_name}"}

        return {
            "name": note.name,
            "title": note.properties.title,
            "tags": note.properties.tags,
            "note_type": note.note_type.name,
            "content": note.content,
            "links": note.links,
        }

    def _tool_find_notes_by_tag(self, tag: str) -> Dict[str, Any]:
        """タグでノートを検索する（メタデータのみ）"""
        notes = self.note_repository.find_by_tag(tag)
        return {
            "count": len(notes),
            "notes": [NoteMetadata.from_note(n).to_dict() for n in notes],
        }

    def _tool_find_notes_by_type(self, note_type_str: str) -> Dict[str, Any]:
        """NoteType でノートを検索する（メタデータのみ）"""
        try:
            note_type = NoteType[note_type_str]
        except KeyError:
            return {"error": f"無効なノートタイプ: {note_type_str}"}

        notes = self.note_repository.find_by_note_type(note_type)
        return {
            "count": len(notes),
            "notes": [NoteMetadata.from_note(n).to_dict() for n in notes],
        }

    def _tool_get_note_links(self, note_name: str) -> Dict[str, Any]:
        """ノートのリンク先を取得する"""
        note = self.note_repository.get_by_file_name(note_name)
        if note is None:
            return {"error": f"ノートが見つかりません: {note_name}"}

        linked_notes = self.note_repository.get_links(note)
        return {
            "source": note_name,
            "count": len(linked_notes),
            "links": [NoteMetadata.from_note(n).to_dict() for n in linked_notes],
        }

    def _tool_search_notes(self, query: str) -> Dict[str, Any]:
        """全文検索する（メタデータのみ）"""
        notes = self.note_repository.search_by_text(query)
        return {
            "query": query,
            "count": len(notes),
            "notes": [NoteMetadata.from_note(n).to_dict() for n in notes],
        }

    # =========================================================================
    # レスポンスパース
    # =========================================================================

    def _parse_tasks_from_json(self, response_text: str) -> List[Task]:
        """Gemini のレスポンス（JSON）を Task リストにパースする

        Args:
            response_text(str): Gemini のレスポンステキスト

        Returns:
            List[Task]: パースされたタスクのリスト
        """
        tasks: List[Task] = []

        # JSON 部分を抽出（```json ... ``` で囲まれている場合に対応）
        json_match = re.search(r"```json\s*(.*?)\s*```", response_text, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            # ```json がない場合はそのままパースを試みる
            json_str = response_text.strip()

        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.error(f"JSON パースエラー: {e}")
            logger.debug(f"レスポンステキスト: {response_text}")
            return tasks

        # TaskType のマッピング
        type_mapping = {
            "Daily": TaskType.Daily,
            "Must": TaskType.Must,
            "Should": TaskType.Should,
            "Could": TaskType.Could,
        }

        task_list = data.get("tasks", [])
        for item in task_list:
            name = item.get("name", "")
            task_type_str = item.get("task_type", "Daily")
            task_type = type_mapping.get(task_type_str, TaskType.Daily)

            if name:
                tasks.append(
                    Task(
                        name=name,
                        task_type=task_type,
                        is_completed=False,
                    )
                )

        logger.debug(f"Gemini レスポンスから {len(tasks)} 件のタスクをパースしました")
        return tasks

    # =========================================================================
    # メイン処理
    # =========================================================================

    def generate_tasks(self, initial_context: InitialContext) -> List[Task]:
        """初期コンテキストからタスクを生成する（ReAct Agent）

        Args:
            initial_context(InitialContext): 初期コンテキスト

        Returns:
            List[Task]: 生成されたタスク
        """
        # システムプロンプトを読み込む
        with open(self.config.prompt_path, "r", encoding="utf-8") as file:
            system_prompt = file.read()

        # 初期コンテキストをフォーマット
        user_prompt = initial_context.format_for_prompt()
        user_prompt += "\n\n上記の情報を元に、今日のタスクを生成してください。"
        user_prompt += "必要に応じてツールを使って追加の情報を取得できます。"

        # ツール定義
        tool_declarations = self._get_tool_declarations()
        tool = types.Tool(function_declarations=tool_declarations)

        # 設定
        # NOTE: AUTO だと Gemini がツール不要と判断した場合に呼び出さない
        # 最初は ANY を使って少なくとも1回はツールを呼び出すことを強制
        # ツール呼び出し後は AUTO に戻して最終回答を得られるようにする
        config_any = types.GenerateContentConfig(
            system_instruction=system_prompt,
            tools=[tool],
            tool_config=types.ToolConfig(
                function_calling_config=types.FunctionCallingConfig(
                    mode=types.FunctionCallingConfigMode.ANY
                )
            ),
        )
        config_auto = types.GenerateContentConfig(
            system_instruction=system_prompt,
            tools=[tool],
            tool_config=types.ToolConfig(
                function_calling_config=types.FunctionCallingConfig(
                    mode=types.FunctionCallingConfigMode.AUTO
                )
            ),
        )

        # 会話履歴
        contents: List[types.Content] = [
            types.Content(role="user", parts=[types.Part.from_text(text=user_prompt)])
        ]

        # Function Calling ループ
        tool_call_count = 0

        while tool_call_count < self.config.max_tool_calls:
            # 最初の呼び出しはANY（ツール強制）、その後はAUTO（柔軟）
            current_config = config_any if tool_call_count == 0 else config_auto
            logger.debug(f"Gemini API 呼び出し (ツール呼び出し回数: {tool_call_count}, mode: {'ANY' if tool_call_count == 0 else 'AUTO'})")

            response = self.client.models.generate_content(
                model=self.config.model,
                contents=contents,
                config=current_config,
            )

            # レスポンスを会話履歴に追加
            if response.candidates and response.candidates[0].content:
                contents.append(response.candidates[0].content)

            # Function Call があるか確認
            function_calls = response.function_calls

            if not function_calls:
                # Function Call がない = 最終回答
                logger.info(f"最終回答を取得 (ツール呼び出し回数: {tool_call_count})")
                break

            # Function Call を実行
            function_responses = []
            for fn_call in function_calls:
                tool_call_count += 1
                fn_name = fn_call.name or ""
                fn_args = dict(fn_call.args) if fn_call.args else {}
                logger.info(f"ツール呼び出し [{tool_call_count}]: {fn_name}")

                result = self._execute_tool(fn_name, fn_args)
                function_responses.append(
                    types.Part.from_function_response(
                        name=fn_name,
                        response=result,
                    )
                )

            # Function Response を会話履歴に追加
            contents.append(types.Content(role="user", parts=function_responses))

        # 最大回数に達した場合
        if tool_call_count >= self.config.max_tool_calls:
            logger.warning(
                f"ツール呼び出しが最大回数 ({self.config.max_tool_calls}) に達しました"
            )

        # 最終レスポンスからタスクをパース
        final_text = response.text if response.text else ""
        tasks = self._parse_tasks_from_json(final_text)

        return tasks
