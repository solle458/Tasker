from typing import List

from src.usecase.generate_daily_tasks import GenerateDailyTasksUseCase
from src.infrastructure.config import Config
from src.infrastructure.repositories.google_calendar_repository import GoogleCalendarRepository
from src.infrastructure.repositories.gemini_repository import GeminiRepository
from src.infrastructure.repositories.obsidian_repository import ObsidianRepository
from src.domain.models.task import Task, TaskType


def format_tasks_as_markdown(tasks: List[Task]) -> str:
    """タスクをMarkdown形式に変換する

    Args:
        tasks(List[Task]): タスクのリスト

    Returns:
        str: Markdown形式のタスク文字列
    """
    output = "## Task\n\n"
    for task_type in [TaskType.Daily, TaskType.Must, TaskType.Should, TaskType.Could]:
        type_tasks = [t for t in tasks if t.task_type == task_type]
        if type_tasks:
            output += f"### {task_type.name}\n"
            for task in type_tasks:
                checkbox = "[x]" if task.is_completed else "[ ]"
                output += f"- {checkbox} {task.name}\n"
            output += "\n"
    return output.strip()


def main():
    config = Config()
    google_calendar_repository = GoogleCalendarRepository(config.google_calendar)
    obsidian_repository = ObsidianRepository(config.obsidian.vault_path)
    gemini_repository = GeminiRepository(config.gemini, obsidian_repository)
    generate_daily_tasks_use_case = GenerateDailyTasksUseCase(google_calendar_repository, obsidian_repository, gemini_repository)
    tasks = generate_daily_tasks_use_case.exec()
    print(format_tasks_as_markdown(tasks))

if __name__ == "__main__":
    main()
