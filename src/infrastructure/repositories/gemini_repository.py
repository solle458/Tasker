import json
import logging
import re
from google import genai
from typing import List

from src.domain.models.task import Task, TaskType
from src.domain.models.note import Note
from src.domain.models.calendar import Event
from src.domain.repository.reasoning_repository import ReasoningRepository
from src.infrastructure.config import GeminiConfig

logger = logging.getLogger(__name__)


class GeminiRepository(ReasoningRepository):
    """Gemini のリポジトリ
    Args:
        config(GeminiConfig): 設定
    """

    def __init__(self, config: GeminiConfig) -> None:
        self.config = config
        self.client = genai.Client(api_key=self.config.api_key)

    def _format(
        self,
        arhievment_rate: float,
        relevant_notes: List[Note],
        events: List[Event],
    ) -> str:
        """プロンプトをフォーマットする
        Args:
            arhievment_rate(float): 達成率
            relevant_notes(List[Note]): 関連するノート
            events(List[Event]): イベント
        Returns:
            str: フォーマットされたプロンプト
        """
        # ノート情報を文字列化
        notes_str = (
            "\n".join(
                [
                    f"- {note.properties.title}: {note.content[:200]}..."
                    for note in relevant_notes
                ]
            )
            if relevant_notes
            else "なし"
        )

        # イベント情報を文字列化
        events_str = (
            "\n".join(
                [f"- {event.name} ({event.start} ~ {event.end})" for event in events]
            )
            if events
            else "なし"
        )

        return f"""
## 入力データ
- 昨日の達成率: {arhievment_rate:.1%}
- 関連するノート:
{notes_str}
- 今日の予定:
{events_str}

## 出力形式
以下の JSON 形式で出力してください。JSON のみを出力し、それ以外のテキストは含めないでください。

```json
{{
  "tasks": [
    {{"name": "タスク名", "task_type": "Must"}},
    {{"name": "タスク名", "task_type": "Should"}},
    {{"name": "タスク名", "task_type": "Could"}},
    {{"name": "タスク名", "task_type": "Daily"}}
  ]
}}
```

task_type は以下のいずれかを指定してください:
- Daily: 毎日のルーティン
- Must: 必須タスク
- Should: やるべきタスク
- Could: できればやるタスク
"""

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

    def generate_tasks(
        self, arhievment_rate: float, relevant_notes: List[Note], events: List[Event]
    ) -> List[Task]:
        """達成率と関連するノートからタスクを生成する
        Args:
            arhievment_rate(float): 達成率
            relevant_notes(List[Note]): 関連するノート
            events(List[Event]): イベント
        Returns:
            List[Task]: 生成されたタスク
        """
        with open(self.config.prompt_path, "r") as file:
            prompt = file.read()
        prompt += "\n" + self._format(
            arhievment_rate=arhievment_rate,
            relevant_notes=relevant_notes,
            events=events,
        )
        response = self.client.models.generate_content(
            model=self.config.model, contents=prompt
        )
        tasks = self._parse_tasks_from_json(str(response.text))
        return tasks
