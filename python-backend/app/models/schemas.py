"""
Pydantic schemas for API request/response validation
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime


class CaseCreate(BaseModel):
    """Schema for creating a new case"""
    case_name: str = Field(..., min_length=1, max_length=255)
    evidence_number: Optional[str] = None
    timezone: str = "UTC"
    input_folder: str
    output_folder: str


class CaseResponse(BaseModel):
    """Schema for case response"""
    id: str
    case_name: str
    evidence_number: Optional[str]
    timezone: str
    status: str
    processed_files: int
    total_files: int
    total_transactions: int
    date_range: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ProcessingStatus(BaseModel):
    """Schema for processing status"""
    case_id: str
    status: str
    progress: float
    current_file: Optional[str]
    message: str


class ChatRequest(BaseModel):
    """Schema for chat request"""
    question: str = Field(..., min_length=1)


class ChatResponse(BaseModel):
    """Schema for chat response"""
    question: str
    answer: str
    model: str
    timestamp: datetime


class AnalysisInsights(BaseModel):
    """Schema for analysis insights"""
    total_transactions: int
    total_debit: float
    total_credit: float
    date_range: Dict[str, str]
    categories: Dict[str, float]
    monthly_trend: Dict[str, float]
    top_counterparties: List[Dict[str, any]]


class NetworkNode(BaseModel):
    """Schema for network graph node"""
    id: str
    label: str
    group: str


class NetworkEdge(BaseModel):
    """Schema for network graph edge"""
    from_node: str = Field(..., alias="from")
    to_node: str = Field(..., alias="to")
    amount: float
    count: int


class NetworkData(BaseModel):
    """Schema for network visualization data"""
    nodes: List[NetworkNode]
    edges: List[NetworkEdge]
