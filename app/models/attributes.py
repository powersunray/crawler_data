from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy import Column, String, ForeignKey
from uuid import uuid4
from app import db

class Attribute(db.Model):
    __tablename__ = "attributes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4, unique=True, nullable=False)
    name = Column(String(255), nullable=False)  
    type = Column(String(255), nullable=False)  
    description = Column(String(255), nullable=False)
    source_id =  db.Column(UUID(as_uuid=True), ForeignKey('sources.id'), nullable=False)