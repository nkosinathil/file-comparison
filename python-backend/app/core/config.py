"""
Application Configuration

Loads settings from environment variables using Pydantic Settings.
All configuration is centralized here for easy management.
"""

from typing import List
from pydantic_settings import BaseSettings
from pydantic import validator


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    
    Values are loaded from .env file or environment.
    See deploy/env-examples/.env.python-backend.example for all options.
    """
    
    # Application Settings
    APP_NAME: str = "Aurex Python Backend"
    APP_VERSION: str = "1.0.0"
    APP_ENV: str = "production"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    
    # FastAPI Settings
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8001
    API_WORKERS: int = 4
    API_RELOAD: bool = False
    
    # Security
    API_SECRET_KEY: str
    INTERNAL_API_KEY: str
    CORS_ORIGINS: List[str] = ["http://192.168.1.66"]
    
    @validator("CORS_ORIGINS", pre=True)
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v
    
    # Database (PostgreSQL)
    DB_HOST: str = "192.168.1.66"
    DB_PORT: int = 5432
    DB_NAME: str = "aurex_db"
    DB_USER: str = "aurex_app_user"
    DB_PASSWORD: str
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    
    @property
    def database_url(self) -> str:
        """Construct PostgreSQL connection URL"""
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    
    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str = ""
    REDIS_DB: int = 0
    
    @property
    def redis_url(self) -> str:
        """Construct Redis connection URL"""
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
    
    # Celery
    CELERY_BROKER_URL: str = ""
    CELERY_RESULT_BACKEND: str = ""
    CELERY_TASK_SERIALIZER: str = "json"
    CELERY_RESULT_SERIALIZER: str = "json"
    CELERY_ACCEPT_CONTENT: List[str] = ["json"]
    CELERY_TIMEZONE: str = "UTC"
    CELERY_ENABLE_UTC: bool = True
    CELERY_WORKER_CONCURRENCY: int = 4
    CELERY_WORKER_PREFETCH_MULTIPLIER: int = 1
    CELERY_TASK_TIME_LIMIT: int = 3600  # 1 hour
    CELERY_TASK_SOFT_TIME_LIMIT: int = 3300  # 55 minutes
    
    @validator("CELERY_BROKER_URL", pre=True)
    def set_celery_broker(cls, v, values):
        if not v:
            return values.get("redis_url", "redis://localhost:6379/0")
        return v
    
    @validator("CELERY_RESULT_BACKEND", pre=True)
    def set_celery_backend(cls, v, values):
        if not v:
            return values.get("redis_url", "redis://localhost:6379/0")
        return v
    
    # MinIO
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str
    MINIO_SECRET_KEY: str
    MINIO_SECURE: bool = False
    MINIO_BUCKET_UPLOADS: str = "aurex-uploads"
    MINIO_BUCKET_RESULTS: str = "aurex-results"
    MINIO_BUCKET_EXPORTS: str = "aurex-exports"
    MINIO_REGION: str = "us-east-1"
    
    # File Processing
    MAX_UPLOAD_SIZE_MB: int = 100
    ALLOWED_FILE_EXTENSIONS: List[str] = ["pdf"]
    TEMP_UPLOAD_DIR: str = "/tmp/aurex/uploads"
    TEMP_PROCESSING_DIR: str = "/tmp/aurex/processing"
    
    @validator("ALLOWED_FILE_EXTENSIONS", pre=True)
    def parse_extensions(cls, v):
        if isinstance(v, str):
            return [ext.strip() for ext in v.split(",")]
        return v
    
    # AI Chat
    ENABLE_AI_CHAT: bool = True
    OLLAMA_ENDPOINT: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama2"
    OLLAMA_TIMEOUT: int = 120
    
    # PDF Processing
    PDF_DPI: int = 300
    TESSERACT_PATH: str = "/usr/bin/tesseract"
    ENABLE_OCR_FALLBACK: bool = True
    
    # Logging
    LOG_FILE_PATH: str = "/var/log/aurex/backend.log"
    LOG_FILE_MAX_BYTES: int = 10485760  # 10MB
    LOG_FILE_BACKUP_COUNT: int = 5
    ENABLE_REQUEST_LOGGING: bool = True
    ENABLE_PERFORMANCE_LOGGING: bool = True
    
    # Feature Flags
    ENABLE_NETWORK_GRAPH: bool = True
    ENABLE_CATEGORY_AUTO_CLASSIFICATION: bool = True
    ENABLE_DUPLICATE_DETECTION: bool = True
    
    # Paths
    LEGACY_SCRIPTS_DIR: str = "/opt/aurex/python-backend/app/legacy_logic"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Create global settings instance
settings = Settings()
