"""
Aurex Python Backend - FastAPI Application Entry Point

This is the main FastAPI application that provides REST API endpoints
for the PHP frontend to communicate with the Python processing backend.
"""

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
import time
import logging

from app.core.config import settings
from app.core.logging_config import setup_logging
from app.api import health, upload, process, jobs, cases

# Set up structured logging
setup_logging()
logger = logging.getLogger(__name__)


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Backend API for Aurex bank statement analysis platform",
    docs_url="/docs" if settings.DEBUG else None,  # Disable docs in production
    redoc_url="/redoc" if settings.DEBUG else None,
)


# =============================================================================
# Middleware Configuration
# =============================================================================

# CORS - Allow requests from PHP application server
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["*"],
)

# GZip compression for responses
app.add_middleware(GZipMiddleware, minimum_size=1000)


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """
    Log all incoming requests with timing information.
    
    This helps with debugging and performance monitoring.
    """
    start_time = time.time()
    
    # Log request
    logger.info(
        "Request started",
        extra={
            "method": request.method,
            "path": request.url.path,
            "client": request.client.host if request.client else None,
        }
    )
    
    # Process request
    response = await call_next(request)
    
    # Calculate duration
    duration_ms = (time.time() - start_time) * 1000
    
    # Log response
    logger.info(
        "Request completed",
        extra={
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_ms": round(duration_ms, 2),
        }
    )
    
    # Add timing header
    response.headers["X-Process-Time"] = str(duration_ms)
    
    return response


# =============================================================================
# Error Handlers
# =============================================================================

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Global exception handler to catch unhandled errors.
    
    Returns a structured JSON response and logs the error.
    """
    logger.error(
        "Unhandled exception",
        extra={
            "method": request.method,
            "path": request.url.path,
            "error": str(exc),
        },
        exc_info=True,
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": "Internal server error",
            "message": str(exc) if settings.DEBUG else "An unexpected error occurred",
        },
    )


# =============================================================================
# Startup and Shutdown Events
# =============================================================================

@app.on_event("startup")
async def startup_event():
    """
    Runs when the application starts.
    
    Initialize connections, verify dependencies, etc.
    """
    logger.info(
        "Application starting",
        extra={
            "app_name": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "environment": settings.APP_ENV,
            "debug": settings.DEBUG,
        }
    )
    
    # TODO: Verify database connection
    # TODO: Verify MinIO connection
    # TODO: Verify Redis connection
    
    logger.info("Application startup complete")


@app.on_event("shutdown")
async def shutdown_event():
    """
    Runs when the application shuts down.
    
    Clean up resources, close connections, etc.
    """
    logger.info("Application shutting down")
    
    # TODO: Close database connections
    # TODO: Close MinIO connections
    # TODO: Close Redis connections
    
    logger.info("Application shutdown complete")


# =============================================================================
# Route Registration
# =============================================================================

# Include API routers
app.include_router(health.router, prefix="/api", tags=["Health"])
app.include_router(upload.router, prefix="/api", tags=["Upload"])
app.include_router(process.router, prefix="/api", tags=["Process"])
app.include_router(jobs.router, prefix="/api", tags=["Jobs"])
app.include_router(cases.router, prefix="/api", tags=["Cases"])


# =============================================================================
# Root Endpoint
# =============================================================================

@app.get("/")
async def root():
    """
    Root endpoint - provides basic API information.
    """
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "docs": "/docs" if settings.DEBUG else None,
    }


# =============================================================================
# Main Entry Point (for development)
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.API_RELOAD,
        log_level=settings.LOG_LEVEL.lower(),
    )
