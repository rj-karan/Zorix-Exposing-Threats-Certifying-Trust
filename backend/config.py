import os
from pydantic_settings import BaseSettings
from pydantic import field_validator, computed_field
from functools import lru_cache
from typing import Optional


class Settings(BaseSettings):
    """Application configuration."""

    # Database
    DATABASE_TYPE: str = "sqlite"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "zorix"
    POSTGRES_USER: str = "zorix_user"
    POSTGRES_PASSWORD: str = "zorix_password"

    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # GitHub
    GITHUB_TOKEN: Optional[str] = None

    # AI/LLM
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "mistral"
    OLLAMA_TIMEOUT: int = 180

    # App
    DEBUG: bool = False
    ALLOWED_ORIGINS: list[str] = ["http://localhost:3000"]

    class Config:
        env_file = ".env"
        extra = "ignore"

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def parse_origins(cls, v):
        if isinstance(v, list):
            return v
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    @computed_field
    @property
    def DATABASE_URL(self) -> str:
        """Construct database URL."""
        if self.DATABASE_TYPE == "postgres":
            return (
                f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@"
                f"{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
            )
        else:
            # SQLite for local development
            return "sqlite+aiosqlite:///./app.db"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings."""
    return Settings()
