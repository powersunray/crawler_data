from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy import Column, String, Float, DateTime, func, ForeignKey
from uuid import uuid4
from app import db

class Result(db.Model):
    __tablename__ = "results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    source_id = Column(UUID(as_uuid=True), ForeignKey("sources.id"), nullable=False)
    status = Column(String(20), nullable=False, default="success")
    processed_content = Column(JSONB)
    processing_time = Column(Float)
    created_at = Column(DateTime(timezone=True), server_default=func.now())