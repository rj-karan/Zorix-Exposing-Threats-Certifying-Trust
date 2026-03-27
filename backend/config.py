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

    # AI/LLM — Ollama is default (free, locally hosted)
    AI_PROVIDER: str = "ollama"  # ollama | anthropic | openai
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "mistral"
    OLLAMA_TIMEOUT: int = 180
    AI_MODEL: str = "mistral"          # unified model name
    ANTHROPIC_API_KEY: str = ""
    OPENAI_API_KEY: str = ""

    # External APIs
    NVD_API_KEY: str = ""
    NVD_API_URL: str = "https://services.nvd.nist.gov/rest/json/cves/2.0"

    # Docker Sandbox
    DOCKER_SOCKET: str = "unix:///var/run/docker.sock"
    SANDBOX_IMAGE: str = "zorix-sandbox:latest"
    SANDBOX_TIMEOUT: int = 60
    SANDBOX_MEMORY: str = "512m"
    SANDBOX_CPUS: float = 0.5

    # Storage
    SNAPSHOT_DIR: str = "./tmp/snapshots"
    EXPLOIT_DIR: str = "./tmp/exploits"
    REPORTS_DIR: str = "./reports"
    LOGS_DIR: str = "./logs"

    # Scanning tools
    BANDIT_ENABLED: bool = True
    SEMGREP_ENABLED: bool = True
    NUCLEI_ENABLED: bool = False
    BANDIT_PATH: str = "bandit"
    SEMGREP_PATH: str = "semgrep"
    NUCLEI_PATH: str = "nuclei"

    # App
    DEBUG: bool = False
    ALLOWED_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:5173"]

    # Notifications
    DEFAULT_WEBHOOK_URL: str = ""
    EMAIL_NOTIFICATIONS: bool = False
    NOTIFICATION_EMAIL: str = ""

    class Config:
        env_file = ".env"
        extra = "ignore"

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def parse_origins(cls, v):
        if isinstance(v, list):
            return v
        if isinstance(v, str):
            import json
            # Try JSON parse first (handles ["url1","url2"] format)
            try:
                parsed = json.loads(v)
                if isinstance(parsed, list):
                    return [str(x).strip() for x in parsed]
            except (json.JSONDecodeError, ValueError):
                pass
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
