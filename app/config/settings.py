"""Application configuration using Pydantic Settings."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    APP_NAME: str = "AI Service"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"

    # MongoDB
    MONGODB_URI: str = "mongodb://localhost:27017"
    MONGODB_DB_NAME: str = "ai_service"

    # JWT
    JWT_SECRET_KEY: str  # Required, no default for security
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_DAYS: int = 3


@lru_cache
def get_settings() -> Settings:
    """Dependency injection function for settings.

    Uses lru_cache to ensure settings are only loaded once.
    """
    return Settings()
