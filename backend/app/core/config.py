from pathlib import Path

from pydantic_settings import BaseSettings

# Project root is two levels up from this file (config.py -> core -> app -> backend -> root)
_PROJECT_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://ossearch:ossearch_dev@localhost:5432/ossearch"
    REDIS_URL: str = "redis://localhost:6379/0"
    GITHUB_TOKEN: str = ""
    OPENAI_API_KEY: str = ""

    SCRAPE_INTERVAL_HOURS: int = 12
    ISSUES_PER_REPO: int = 100

    API_V1_PREFIX: str = "/api/v1"
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]

    class Config:
        env_file = str(_PROJECT_ROOT / ".env")


settings = Settings()
