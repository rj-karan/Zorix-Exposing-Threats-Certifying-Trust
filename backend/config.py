import os
from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional


class Settings(BaseSettings):
    """Application configuration."""

    # Database
    DATABASE_TYPE: str = os.getenv("DATABASE_TYPE", "sqlite")  # sqlite or postgres
    POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "localhost")
    POSTGRES_PORT: int = int(os.getenv("POSTGRES_PORT", 5432))
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "zorix")
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "zorix_user")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "zorix_password")

    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # GitHub
    GITHUB_TOKEN: Optional[str] = os.getenv("GITHUB_TOKEN", None)

    # App
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    ALLOWED_ORIGINS: list[str] = [
        origin.strip() for origin in (os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(","))
    ]

    class Config:
        env_file = ".env"

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
