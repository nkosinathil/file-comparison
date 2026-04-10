"""
Database models using SQLAlchemy
"""

from sqlalchemy import Column, Integer, String, DateTime, JSON, Text, Float, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()


class Case(Base):
    """Case model for tracking bank statement analysis cases"""
    __tablename__ = "cases"
    
    id = Column(String(64), primary_key=True)
    case_name = Column(String(255), nullable=False)
    evidence_number = Column(String(255))
    timezone = Column(String(50), default="UTC")
    status = Column(String(50), default="pending")  # pending, processing, completed, error, cancelled
    
    input_folder = Column(Text)
    output_folder = Column(Text)
    db_path = Column(Text)
    
    processed_files = Column(Integer, default=0)
    total_files = Column(Integer, default=0)
    total_transactions = Column(Integer, default=0)
    date_range = Column(String(100))
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    processing_logs = relationship("ProcessingLog", back_populates="case")
    chat_messages = relationship("ChatMessage", back_populates="case")


class ProcessingLog(Base):
    """Processing logs for cases"""
    __tablename__ = "processing_logs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    case_id = Column(String(64), ForeignKey("cases.id"))
    timestamp = Column(DateTime, default=datetime.utcnow)
    level = Column(String(20))  # INFO, WARNING, ERROR
    message = Column(Text)
    
    case = relationship("Case", back_populates="processing_logs")


class ChatMessage(Base):
    """Chat messages for AI interaction"""
    __tablename__ = "chat_messages"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    case_id = Column(String(64), ForeignKey("cases.id"))
    timestamp = Column(DateTime, default=datetime.utcnow)
    question = Column(Text, nullable=False)
    answer = Column(Text)
    model = Column(String(100))
    
    case = relationship("Case", back_populates="chat_messages")


class Transaction(Base):
    """Bank transactions extracted from statements"""
    __tablename__ = "transactions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    case_id = Column(String(64), ForeignKey("cases.id"))
    
    account_number = Column(String(50))
    transaction_date = Column(DateTime)
    description = Column(Text)
    amount = Column(Float)
    balance = Column(Float)
    transaction_type = Column(String(50))  # debit, credit
    category = Column(String(100))
    counterparty = Column(String(255))
    
    created_at = Column(DateTime, default=datetime.utcnow)
