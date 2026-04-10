"""
Chat Router - Handle AI chat interactions
"""

from fastapi import APIRouter, HTTPException
from ..models.schemas import ChatRequest, ChatResponse
from datetime import datetime

router = APIRouter()


@router.post("/{case_id}/ask", response_model=ChatResponse)
async def ask_question(case_id: str, request: ChatRequest):
    """Ask AI a question about the case"""
    # TODO: Implement AI chat
    # 1. Validate case exists
    # 2. Get case context (transactions, insights)
    # 3. Query Ollama/LLM
    # 4. Store message in database
    # 5. Return response
    
    return ChatResponse(
        question=request.question,
        answer="AI integration pending - Ollama connection to be implemented",
        model="pending",
        timestamp=datetime.utcnow()
    )


@router.get("/{case_id}/history")
async def get_chat_history(case_id: str, limit: int = 50):
    """Get chat history for a case"""
    # TODO: Implement chat history retrieval
    return {
        "case_id": case_id,
        "messages": []
    }
