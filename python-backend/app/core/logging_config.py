"""
Logging Configuration

Sets up structured logging using Python's standard logging module
with JSON formatting for production environments.
"""

import logging
import logging.handlers
import sys
from pathlib import Path

from pythonjsonlogger import jsonlogger

from app.core.config import settings


def setup_logging():
    """
    Configure application logging.
    
    - Console output: Human-readable in development, JSON in production
    - File output: JSON format with rotation
    - Log level: Configurable via environment
    """
    
    # Create logger
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO))
    
    # Remove existing handlers
    logger.handlers = []
    
    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG if settings.DEBUG else logging.INFO)
    
    if settings.APP_ENV == "production":
        # JSON format for production (easier to parse)
        json_formatter = jsonlogger.JsonFormatter(
            "%(asctime)s %(name)s %(levelname)s %(message)s",
            rename_fields={"asctime": "timestamp", "levelname": "level"},
        )
        console_handler.setFormatter(json_formatter)
    else:
        # Human-readable format for development
        console_formatter = logging.Formatter(
            "[%(asctime)s] %(levelname)-8s [%(name)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        console_handler.setFormatter(console_formatter)
    
    logger.addHandler(console_handler)
    
    # File Handler (only if log file path is accessible)
    try:
        log_file = Path(settings.LOG_FILE_PATH)
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.handlers.RotatingFileHandler(
            filename=str(log_file),
            maxBytes=settings.LOG_FILE_MAX_BYTES,
            backupCount=settings.LOG_FILE_BACKUP_COUNT,
            encoding="utf-8",
        )
        file_handler.setLevel(logging.INFO)
        
        # Always use JSON format for file logs
        json_formatter = jsonlogger.JsonFormatter(
            "%(asctime)s %(name)s %(levelname)s %(message)s %(pathname)s %(lineno)d",
            rename_fields={"asctime": "timestamp", "levelname": "level"},
        )
        file_handler.setFormatter(json_formatter)
        
        logger.addHandler(file_handler)
        
    except (OSError, PermissionError) as e:
        # If we can't write to log file, log to console only
        logger.warning(f"Could not set up file logging: {e}")
    
    # Log initial startup
    logger.info(
        "Logging configured",
        extra={
            "app_name": settings.APP_NAME,
            "environment": settings.APP_ENV,
            "log_level": settings.LOG_LEVEL,
        }
    )


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a specific module.
    
    Args:
        name: Module name (usually __name__)
    
    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)
