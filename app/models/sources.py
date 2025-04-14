from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy import Column, String, Boolean, DateTime, func, ForeignKey
from uuid import uuid4
from app import db

class Source(db.Model):
    __tablename__ = "sources"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(100), nullable=False)
    url = Column(String(255), nullable=False)
    description = Column(String)
    selectors = Column(JSONB, nullable=False)
    is_active = Column(Boolean, default=True)