"""
Health Check Endpoint

Provides system health status for monitoring and load balancers.
"""

from fastapi import APIRouter, status
from pydantic import BaseModel
from datetime import datetime
import psutil
import logging

from app.core.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)


class HealthResponse(BaseModel):
    """Health check response model"""
    status: str
    timestamp: datetime
    version: str
    environment: str
    checks: dict


@router.get("/health", response_model=HealthResponse, status_code=status.HTTP_200_OK)
async def health_check():
    """
    Health check endpoint.
    
    Returns system health status including:
    - Application status
    - Database connectivity (TODO)
    - Redis connectivity (TODO)
    - MinIO connectivity (TODO)
    - System resources
    
    This endpoint can be used by:
    - Load balancers for health checks
    - Monitoring systems
    - Developers for debugging
    """
    
    # Get system stats
    cpu_percent = psutil.cpu_percent(interval=0.1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    checks = {
        "application": "healthy",
        "system": {
            "cpu_percent": cpu_percent,
            "memory_percent": memory.percent,
            "memory_available_mb": round(memory.available / 1024 / 1024, 2),
            "disk_percent": disk.percent,
            "disk_free_gb": round(disk.free / 1024 / 1024 / 1024, 2),
        },
    }
    
    # TODO: Add database health check
    # checks["database"] = "healthy" | "unhealthy"
    
    # TODO: Add Redis health check
    # checks["redis"] = "healthy" | "unhealthy"
    
    # TODO: Add MinIO health check
    # checks["minio"] = "healthy" | "unhealthy"
    
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow(),
        version=settings.APP_VERSION,
        environment=settings.APP_ENV,
        checks=checks,
    )


@router.get("/ping", status_code=status.HTTP_200_OK)
async def ping():
    """
    Simple ping endpoint for basic connectivity testing.
    
    Returns:
        {"ping": "pong"}
    """
    return {"ping": "pong"}
