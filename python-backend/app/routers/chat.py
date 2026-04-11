"""
Chat Router - Handle AI chat interactions
"""

from fastapi import APIRouter, Depends, HTTPException
from ..models.schemas import ChatRequest, ChatResponse
from datetime import datetime
from sqlalchemy.orm import Session

from ..config import settings
from ..models.database import Case, ChatMessage, get_db

router = APIRouter()


@router.post("/{case_id}/ask", response_model=ChatResponse)
async def ask_question(case_id: str, request: ChatRequest, db: Session = Depends(get_db)):
    """Ask AI a question about the case"""
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    answer = "AI integration pending - Ollama connection to be implemented"
    message = ChatMessage(
        case_id=case_id,
        question=request.question,
        answer=answer,
        model=settings.OLLAMA_MODEL,
    )
    db.add(message)
    db.commit()
    db.refresh(message)

    return ChatResponse(
        question=request.question,
        answer=message.answer,
        model=message.model or settings.OLLAMA_MODEL,
        timestamp=message.timestamp or datetime.utcnow(),
    )


@router.get("/{case_id}/history")
async def get_chat_history(
    case_id: str,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    """Get chat history for a case"""
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.case_id == case_id)
        .order_by(ChatMessage.timestamp.desc())
        .limit(min(max(limit, 1), 200))
        .all()
    )
    return {
        "case_id": case_id,
        "messages": [
            {
                "id": message.id,
                "timestamp": message.timestamp,
                "question": message.question,
                "answer": message.answer,
                "model": message.model,
            }
            for message in messages
        ]
    }
