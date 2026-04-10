"""
Configuration Management
"""

from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Application settings"""
    
    # App
    APP_NAME: str = "Aurex Backend"
    DEBUG: bool = False
    API_KEY: str = "change-this-in-production"
    
    # Database
    DATABASE_URL: str = "postgresql://aurex:password@localhost:5432/aurex"
    
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
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
