"""Application configuration."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # OpenAI
    openai_api_key: str = ""

    # Database
    postgres_url: str = "postgresql://user:pass@localhost:5432/travel"
    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: str = ""

    # Search (optional)
    tavily_api_key: str = ""
    serpapi_api_key: str = ""

    # App
    log_level: str = "INFO"
    env: str = "development"

    # CORS
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:5173"]


settings = Settings()
