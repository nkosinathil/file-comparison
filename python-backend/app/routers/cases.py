"""
Cases Router - Handle case CRUD operations
"""

from datetime import datetime
from typing import List
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from ..models.database import Case, get_db
from ..models.schemas import CaseCreate, CaseResponse

router = APIRouter()


@router.get("/", response_model=List[CaseResponse])
async def list_cases(
    skip: int = 0,
    limit: int = 100,
    status: str = None,
    db: Session = Depends(get_db),
):
    """List all cases with optional filtering"""
    query = db.query(Case)
    if status:
        query = query.filter(Case.status == status)

    cases = (
        query.order_by(Case.created_at.desc())
        .offset(max(skip, 0))
        .limit(min(max(limit, 1), 1000))
        .all()
    )
    return cases


@router.post("/", response_model=CaseResponse, status_code=201)
async def create_case(case: CaseCreate, db: Session = Depends(get_db)):
    """Create a new case"""
    now = datetime.utcnow()
    case_id = f"CASE_{now.strftime('%Y%m%d_%H%M%S')}_{uuid4().hex[:8].upper()}"
    db_case = Case(
        id=case_id,
        case_name=case.case_name,
        evidence_number=case.evidence_number,
        timezone=case.timezone,
        status="pending",
        input_folder=case.input_folder,
        output_folder=case.output_folder,
        processed_files=0,
        total_files=0,
        total_transactions=0,
        created_at=now,
        updated_at=now,
    )
    db.add(db_case)
    db.commit()
    db.refresh(db_case)
    return db_case


@router.get("/{case_id}", response_model=CaseResponse)
async def get_case(case_id: str, db: Session = Depends(get_db)):
    """Get case details by ID"""
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    return case


@router.delete("/{case_id}")
async def delete_case(case_id: str, db: Session = Depends(get_db)):
    """Delete a case"""
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    db.delete(case)
    db.commit()
    return {"case_id": case_id, "status": "deleted"}
