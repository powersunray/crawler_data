from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy import Column, String, Boolean, DateTime, func, ForeignKey
from uuid import uuid4
from app import db

class Attribute(db.Model):
    __tablename__ = "attributes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    keyword = Column(String(50), unique=True, nullable=False)
    source_id = Column(UUID(as_uuid=True), ForeignKey("sources.id"), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())