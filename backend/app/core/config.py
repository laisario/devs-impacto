"""
Application configuration via environment variables.
Uses pydantic-settings for validation and type coercion.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # MongoDB
    mongodb_uri: str = "mongodb://localhost:27017"
    database_name: str = "pnae_dev"

    # JWT Authentication
    jwt_secret: str = "your-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 1440  # 24 hours

    # Storage Provider
    storage_provider: str = "mock"  # mock | s3 | gcs
    mock_storage_base_url: str = "http://localhost:8000/mock-storage"

    # OTP Settings (mock)
    otp_code_mock: str = "123456"  # Fixed OTP for development
    otp_expire_minutes: int = 5

    # LLM Settings
    openai_api_key: str | None = None
    llm_provider: str = "mock"  # openai | mock | deco
    llm_model: str = "gpt-4o-mini"
    rag_embedding_model: str = "text-embedding-3-small"
    deco_api_url: str = "https://api.decocms.com/hackathon2/belo-projeto/triggers/5013e0dc-38dd-4af8-ad35-8c19cd2094cf"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()

