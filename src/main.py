from src.usecase.generate_daily_tasks import GenerateDailyTasksUseCase
from src.infrastructure.config import Config
from src.infrastructure.repositories.google_calendar_repository import GoogleCalendarRepository
from src.infrastructure.repositories.gemini_repository import GeminiRepository
from src.infrastructure.repositories.obsidian_repository import ObsidianRepository

def main():
    config = Config()
    google_calendar_repository = GoogleCalendarRepository(config.google_calendar)
    obsidian_repository = ObsidianRepository(config.obsidian.vault_path)
    gemini_repository = GeminiRepository(config.gemini, obsidian_repository)
    generate_daily_tasks_use_case = GenerateDailyTasksUseCase(google_calendar_repository, obsidian_repository, gemini_repository)
    tasks = generate_daily_tasks_use_case.exec()
    print(tasks)

if __name__ == "__main__":
    main()
