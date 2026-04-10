"""
Aurex Python Backend - FastAPI Application
Handles PDF processing, AI chat, and data analysis
"""

from fastapi import FastAPI, HTTPException, Depends, Security
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader
from contextlib import asynccontextmanager
import logging
from typing import Optional

from .routers import cases, analysis, chat, processing
from .config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# API Key Security
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

async def verify_api_key(api_key: str = Security(api_key_header)) -> str:
    """Verify API key for requests from PHP frontend"""
    if not api_key or api_key != settings.API_KEY:
        raise HTTPException(status_code=403, detail="Invalid or missing API key")
    return api_key


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    logger.info("Starting Aurex Python Backend...")
    # Initialize services here
    yield
    logger.info("Shutting down Aurex Python Backend...")


# Create FastAPI app
app = FastAPI(
    title="Aurex Backend API",
    description="Python backend for bank statement processing and analysis",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(
    cases.router,
    prefix="/api/cases",
    tags=["cases"],
    dependencies=[Depends(verify_api_key)]
)
app.include_router(
    processing.router,
    prefix="/api/processing",
    tags=["processing"],
    dependencies=[Depends(verify_api_key)]
)
app.include_router(
    analysis.router,
    prefix="/api/analysis",
    tags=["analysis"],
    dependencies=[Depends(verify_api_key)]
)
app.include_router(
    chat.router,
    prefix="/api/chat",
    tags=["chat"],
    dependencies=[Depends(verify_api_key)]
)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Aurex Backend API",
        "version": "1.0.0",
        "status": "operational"
    }


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "aurex-backend"
    }
