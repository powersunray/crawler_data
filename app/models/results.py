from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy import Column, String, DateTime, ForeignKey
from uuid import uuid4
from app import db

class Result(db.Model):
    __tablename__ = "results"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4, unique=True, nullable=False)
    source_id = Column(UUID(as_uuid=True), ForeignKey('sources.id'), nullable=False)  
    url = Column(String(500), nullable=False)  
    contents = Column(JSONB, nullable=False)      
    time_stamp = Column(DateTime, nullable=False)