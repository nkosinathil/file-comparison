"""
Processing Router - Handle PDF processing and job management
"""

from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from sqlalchemy.orm import Session

from ..models.database import Case, get_db
from ..models.schemas import ProcessingStatus

router = APIRouter()


@router.post("/{case_id}/start")
async def start_processing(
    case_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Start processing PDFs for a case"""
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    if case.status in {"processing", "completed"}:
        raise HTTPException(status_code=409, detail=f"Case already {case.status}")

    case.status = "queued"
    case.updated_at = datetime.now(timezone.utc)
    db.commit()

    # Placeholder hook for worker-based processing implementation.
    background_tasks.add_task(lambda: None)

    return {
        "case_id": case_id,
        "status": "queued",
        "message": "Processing started"
    }


@router.get("/{case_id}/status", response_model=ProcessingStatus)
async def get_processing_status(case_id: str, db: Session = Depends(get_db)):
    """Get current processing status"""
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    progress_map = {
        "pending": 0.0,
        "queued": 0.0,
        "processing": 0.5,
        "completed": 1.0,
        "error": 1.0,
        "cancelled": 1.0,
    }
    status = case.status or "pending"
    return ProcessingStatus(
        case_id=case_id,
        status=status,
        progress=progress_map.get(status, 0.0),
        current_file=None,
        message=f"Case is {status}"
    )


@router.post("/{case_id}/cancel")
async def cancel_processing(case_id: str, db: Session = Depends(get_db)):
    """Cancel ongoing processing"""
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    if case.status == "completed":
        raise HTTPException(status_code=409, detail="Completed case cannot be cancelled")

    case.status = "cancelled"
    case.updated_at = datetime.now(timezone.utc)
    db.commit()
    return {
        "case_id": case_id,
        "status": "cancelled",
        "message": "Processing cancelled"
    }
