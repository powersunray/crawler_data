from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Column, String, Integer
from uuid import uuid4
from app import db

class Source(db.Model):
    __tablename__ = "sources"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4, unique=True, nullable=False)
    url = Column(String(500), nullable=False)                
    link_selector = Column(String(255), nullable=False)      
    status = db.Column(String(20), nullable=False, default='ACTIVE')    
    threads = Column(Integer, nullable=False)
    description = Column(String(255), nullable=False)      
    card_information = Column(String(255), nullable=False)  