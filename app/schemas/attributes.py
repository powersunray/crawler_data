from pydantic import BaseModel
from uuid import UUID
from typing import Optional
from datetime import datetime

class AttributeBase(BaseModel):
    keyword: str
    source_id: UUID
    is_active: Optional[bool] = True

class AttributeCreate(AttributeBase):
    pass

class AttributeUpdate(BaseModel):
    keyword: Optional[str]
    source_id: Optional[UUID]
    is_active: Optional[bool]

class AttributeOut(AttributeBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True