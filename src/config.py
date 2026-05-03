from pydantic_settings import BaseSettings

"""
Configuration settings for the AI News Curator application.
This module defines the Settings class, which loads configuration values from environment variables or a .env file.
"""


class Settings(BaseSettings):
    NEWSAPI_KEY: str | None = None
    OLLAMA_BASE_URL: str | None = None
    CHROMA_DB_PATH: str | None = None
    SQLITE_DB_PATH: str | None = None
    FASTMCP_LOG_LEVEL: str | None = None

    class Config:
        env_file = ".env"


settings = Settings()
