"""
FastAPI REST API for Aurex Bank Statement Intelligence
Production-ready API with SSO authentication, WebSocket support, and comprehensive endpoints
"""
from fastapi import FastAPI, HTTPException, Depends, File, UploadFile, WebSocket, WebSocketDisconnect, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uvicorn
import logging
import os
import sys
from pathlib import Path
from datetime import datetime, timedelta
import jwt
import hashlib
import json
import asyncio
from contextlib import asynccontextmanager

# Add parent directory to path to import aurex modules
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from aurex_bank_analyzer.core.case_manager import CaseManager
from api.auth import AuthManager, User, UserInDB, get_current_user, get_current_active_user
from api.processing import ProcessingManager
from api.websocket_manager import ConnectionManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('api.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Global managers
case_manager: Optional[CaseManager] = None
processing_manager: Optional[ProcessingManager] = None
connection_manager = ConnectionManager()
auth_manager: Optional[AuthManager] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize and cleanup application resources"""
    global case_manager, processing_manager, auth_manager
    
    # Startup
    logger.info("Starting Aurex API Server...")
    base_dir = Path(__file__).resolve().parent.parent
    case_manager = CaseManager(base_dir / "aurex_bank_analyzer" / "cases")
    processing_manager = ProcessingManager(base_dir / "aurex_bank_analyzer" / "scripts")
    auth_manager = AuthManager()
    
    logger.info("API Server initialized successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Aurex API Server...")
    if processing_manager:
        await processing_manager.cleanup()
    logger.info("API Server shutdown complete")


# Initialize FastAPI app
app = FastAPI(
    title="Aurex Bank Statement Intelligence API",
    description="Production-ready REST API for bank statement analysis with SSO authentication",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== Pydantic Models ====================

class CaseCreate(BaseModel):
    case_name: str = Field(..., min_length=1, max_length=255)
    evidence_number: str = Field(..., min_length=1, max_length=100)
    investigator: str = Field(..., min_length=1, max_length=255)
    input_folder: str
    output_folder: str


class CaseResponse(BaseModel):
    case_id: str
    case_name: str
    evidence_number: str
    investigator: str
    created_at: str
    status: str
    processed_files: int
    total_files: int
    total_transactions: int
    date_range: str


class ProcessingStatus(BaseModel):
    case_id: str
    status: str
    progress: int
    total: int
    message: str


class ChatRequest(BaseModel):
    case_id: str
    message: str
    conversation_history: Optional[List[Dict[str, str]]] = []


class ChatResponse(BaseModel):
    response: str
    timestamp: str


class AnalysisRequest(BaseModel):
    case_id: str


class AnalysisResponse(BaseModel):
    case_id: str
    insights: Dict[str, Any]
    statistics: Dict[str, Any]
    network_data: Optional[Dict[str, Any]] = None


# ==================== Authentication Endpoints ====================

@app.post("/api/auth/token", tags=["Authentication"])
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    OAuth2 compatible token login with username and password.
    Returns JWT access token for API authentication.
    """
    try:
        user = auth_manager.authenticate_user(form_data.username, form_data.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        access_token = auth_manager.create_access_token(
            data={"sub": user.username, "role": user.role}
        )
        
        logger.info(f"User {user.username} logged in successfully")
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "username": user.username,
                "email": user.email,
                "full_name": user.full_name,
                "role": user.role
            }
        }
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/api/auth/register", tags=["Authentication"])
async def register(
    username: str,
    email: str,
    password: str,
    full_name: str,
    current_user: User = Depends(get_current_active_user)
):
    """
    Register a new user (requires admin privileges)
    """
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized to register users")
    
    try:
        success = auth_manager.create_user(username, email, password, full_name)
        if not success:
            raise HTTPException(status_code=400, detail="Username already exists")
        
        logger.info(f"New user {username} registered by {current_user.username}")
        return {"message": "User created successfully", "username": username}
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/api/auth/me", tags=["Authentication"])
async def get_current_user_info(current_user: User = Depends(get_current_active_user)):
    """Get current user information"""
    return {
        "username": current_user.username,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "role": current_user.role,
        "disabled": current_user.disabled
    }


# ==================== SSO Endpoints ====================

@app.get("/api/sso/oauth/authorize", tags=["SSO"])
async def oauth_authorize(
    client_id: str,
    redirect_uri: str,
    response_type: str = "code",
    scope: str = "openid profile email"
):
    """
    OAuth2 authorization endpoint.
    Initiates OAuth2 authorization flow for SSO.
    """
    try:
        auth_url = auth_manager.initiate_oauth_flow(
            client_id=client_id,
            redirect_uri=redirect_uri,
            response_type=response_type,
            scope=scope
        )
        return {"authorization_url": auth_url}
    except Exception as e:
        logger.error(f"OAuth authorization error: {str(e)}")
        raise HTTPException(status_code=500, detail="OAuth initialization failed")


@app.post("/api/sso/oauth/callback", tags=["SSO"])
async def oauth_callback(code: str, state: str):
    """
    OAuth2 callback endpoint.
    Exchanges authorization code for access token.
    """
    try:
        token_data = auth_manager.handle_oauth_callback(code, state)
        return token_data
    except Exception as e:
        logger.error(f"OAuth callback error: {str(e)}")
        raise HTTPException(status_code=400, detail="OAuth callback failed")


@app.post("/api/sso/saml/login", tags=["SSO"])
async def saml_login(saml_response: str):
    """
    SAML 2.0 login endpoint.
    Processes SAML response and creates session.
    """
    try:
        user_data = auth_manager.process_saml_response(saml_response)
        access_token = auth_manager.create_access_token(
            data={"sub": user_data["username"], "role": user_data.get("role", "user")}
        )
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": user_data
        }
    except Exception as e:
        logger.error(f"SAML login error: {str(e)}")
        raise HTTPException(status_code=400, detail="SAML authentication failed")


# ==================== Case Management Endpoints ====================

@app.get("/api/cases", response_model=List[CaseResponse], tags=["Cases"])
async def list_cases(
    finished_only: bool = False,
    current_user: User = Depends(get_current_active_user)
):
    """List all cases accessible to the current user"""
    try:
        cases = case_manager.list_cases(finished_only=finished_only)
        return [CaseResponse(**case.__dict__) for case in cases]
    except Exception as e:
        logger.error(f"Error listing cases: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve cases")


@app.post("/api/cases", response_model=CaseResponse, tags=["Cases"])
async def create_case(
    case_data: CaseCreate,
    current_user: User = Depends(get_current_active_user)
):
    """Create a new case"""
    try:
        # Validate input folder exists
        if not Path(case_data.input_folder).exists():
            raise HTTPException(status_code=400, detail="Input folder does not exist")
        
        # Create output folder
        Path(case_data.output_folder).mkdir(parents=True, exist_ok=True)
        
        case = case_manager.create_case(
            case_name=case_data.case_name,
            evidence_number=case_data.evidence_number,
            investigator=case_data.investigator,
            input_folder=case_data.input_folder,
            output_folder=case_data.output_folder
        )
        
        logger.info(f"Case {case.case_id} created by {current_user.username}")
        return CaseResponse(**case.__dict__)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating case: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create case")


@app.get("/api/cases/{case_id}", response_model=CaseResponse, tags=["Cases"])
async def get_case(
    case_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Get case details by ID"""
    try:
        case = case_manager.load_case(case_id)
        if not case:
            raise HTTPException(status_code=404, detail="Case not found")
        return CaseResponse(**case.__dict__)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving case: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve case")


@app.delete("/api/cases/{case_id}", tags=["Cases"])
async def delete_case(
    case_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Delete a case (admin only)"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized to delete cases")
    
    try:
        case = case_manager.load_case(case_id)
        if not case:
            raise HTTPException(status_code=404, detail="Case not found")
        
        # Delete case folder
        import shutil
        case_folder = case_manager.cases_dir / case_id
        if case_folder.exists():
            shutil.rmtree(case_folder)
        
        logger.info(f"Case {case_id} deleted by {current_user.username}")
        return {"message": "Case deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting case: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete case")


# ==================== Processing Endpoints ====================

@app.post("/api/cases/{case_id}/process", tags=["Processing"])
async def start_processing(
    case_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Start processing a case"""
    try:
        case = case_manager.load_case(case_id)
        if not case:
            raise HTTPException(status_code=404, detail="Case not found")
        
        await processing_manager.start_processing(case_id, case)
        
        logger.info(f"Processing started for case {case_id} by {current_user.username}")
        return {"message": "Processing started", "case_id": case_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting processing: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to start processing")


@app.post("/api/cases/{case_id}/cancel", tags=["Processing"])
async def cancel_processing(
    case_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Cancel processing for a case"""
    try:
        await processing_manager.cancel_processing(case_id)
        logger.info(f"Processing cancelled for case {case_id} by {current_user.username}")
        return {"message": "Processing cancelled", "case_id": case_id}
    except Exception as e:
        logger.error(f"Error cancelling processing: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to cancel processing")


@app.get("/api/cases/{case_id}/status", response_model=ProcessingStatus, tags=["Processing"])
async def get_processing_status(
    case_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Get processing status for a case"""
    try:
        status_data = await processing_manager.get_status(case_id)
        if not status_data:
            raise HTTPException(status_code=404, detail="Processing status not found")
        return ProcessingStatus(**status_data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting status: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve status")


# ==================== File Upload Endpoints ====================

@app.post("/api/cases/{case_id}/upload", tags=["Files"])
async def upload_files(
    case_id: str,
    files: List[UploadFile] = File(...),
    current_user: User = Depends(get_current_active_user)
):
    """Upload PDF files to a case"""
    try:
        case = case_manager.load_case(case_id)
        if not case:
            raise HTTPException(status_code=404, detail="Case not found")
        
        # Validate and sanitize case input folder path
        input_folder = Path(case.input_folder).resolve()
        
        # Security: Ensure the path is within allowed directories
        # Prevent path traversal attacks
        allowed_base = Path("/app/data").resolve()
        try:
            input_folder.relative_to(allowed_base)
        except ValueError:
            raise HTTPException(
                status_code=400, 
                detail="Invalid input folder path"
            )
        
        input_folder.mkdir(parents=True, exist_ok=True)
        
        uploaded_files = []
        for file in files:
            if not file.filename.endswith('.pdf'):
                logger.warning(f"Skipping non-PDF file: {file.filename}")
                continue
            
            # Sanitize filename to prevent path traversal
            safe_filename = Path(file.filename).name
            if safe_filename != file.filename or '..' in file.filename:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid filename: {file.filename}"
                )
            
            file_path = input_folder / safe_filename
            
            # Additional check to ensure file stays within input folder
            try:
                file_path.resolve().relative_to(input_folder.resolve())
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid file path"
                )
            
            with open(file_path, "wb") as f:
                content = await file.read()
                f.write(content)
            
            uploaded_files.append(safe_filename)
            logger.info(f"File {safe_filename} uploaded to case {case_id}")
        
        return {
            "message": f"Uploaded {len(uploaded_files)} files",
            "files": uploaded_files
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading files: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to upload files")


# ==================== Analysis Endpoints ====================

@app.post("/api/analysis/chat", response_model=ChatResponse, tags=["Analysis"])
async def chat_analysis(
    chat_request: ChatRequest,
    current_user: User = Depends(get_current_active_user)
):
    """Chat with AI assistant about case analysis"""
    try:
        case = case_manager.load_case(chat_request.case_id)
        if not case:
            raise HTTPException(status_code=404, detail="Case not found")
        
        response = await processing_manager.chat_query(
            chat_request.case_id,
            chat_request.message,
            chat_request.conversation_history
        )
        
        return ChatResponse(
            response=response,
            timestamp=datetime.now().isoformat()
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in chat analysis: {str(e)}")
        raise HTTPException(status_code=500, detail="Chat analysis failed")


@app.post("/api/analysis/insights", response_model=AnalysisResponse, tags=["Analysis"])
async def get_insights(
    analysis_request: AnalysisRequest,
    current_user: User = Depends(get_current_active_user)
):
    """Get insights and statistics for a case"""
    try:
        case = case_manager.load_case(analysis_request.case_id)
        if not case:
            raise HTTPException(status_code=404, detail="Case not found")
        
        insights = await processing_manager.get_insights(analysis_request.case_id, case.db_path)
        
        return AnalysisResponse(
            case_id=analysis_request.case_id,
            insights=insights.get("insights", {}),
            statistics=insights.get("statistics", {}),
            network_data=insights.get("network_data")
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting insights: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve insights")


# ==================== WebSocket Endpoints ====================

@app.websocket("/ws/cases/{case_id}/progress")
async def websocket_progress(websocket: WebSocket, case_id: str):
    """WebSocket endpoint for real-time processing progress updates"""
    await connection_manager.connect(websocket, case_id)
    try:
        while True:
            # Keep connection alive and send progress updates
            status = await processing_manager.get_status(case_id)
            if status:
                await websocket.send_json(status)
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        connection_manager.disconnect(websocket, case_id)
        logger.info(f"WebSocket disconnected for case {case_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        connection_manager.disconnect(websocket, case_id)


# ==================== Health Check ====================

@app.get("/api/health", tags=["System"])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }


@app.get("/api/version", tags=["System"])
async def get_version():
    """Get API version information"""
    return {
        "version": "1.0.0",
        "api_name": "Aurex Bank Statement Intelligence API",
        "python_version": sys.version
    }


# ==================== Main Entry Point ====================

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,  # Set to False in production
        workers=4,
        log_level="info",
        access_log=True
    )
