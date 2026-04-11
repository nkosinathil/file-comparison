"""
Configuration Management
"""

from pydantic import AliasChoices, Field, field_validator
from pydantic_settings import BaseSettings
from typing import List, Optional


class Settings(BaseSettings):
    """Application settings"""

    # App
    APP_NAME: str = "Aurex Backend"
    DEBUG: bool = False
    API_KEY: str = Field(
        default="change-this-in-production",
        validation_alias=AliasChoices("API_KEY", "PYTHON_API_KEY"),
    )

    # Database (prefer DATABASE_URL, fallback to DB_* pieces)
    DATABASE_URL: Optional[str] = None
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str = "aurex"
    DB_USER: str = "aurex"
    DB_PASS: str = "change_this_password"

    # Redis Cache
    REDIS_URL: str = "redis://localhost:6379/0"
    CACHE_TTL: int = 3600

    # CORS
    ALLOWED_ORIGINS: List[str] = ["http://localhost", "http://localhost:80"]

    # File Processing
    UPLOAD_DIR: str = "/var/aurex/uploads"
    MAX_UPLOAD_SIZE: int = 52428800  # 50MB
    PROCESSING_WORKERS: int = 4

    # AI/ML
    OLLAMA_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama2"

    # Case Storage
    CASE_STORAGE_PATH: str = "/var/aurex/cases"

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def parse_allowed_origins(cls, value):
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @property
    def database_url(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return (
            f"postgresql+psycopg2://{self.DB_USER}:{self.DB_PASS}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
