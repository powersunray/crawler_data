from pydantic import BaseModel
from uuid import UUID
from typing import Optional, Dict

class SourceBase(BaseModel):
    name: str
    url: str  # Sửa từ HttpUrl thành str
    description: Optional[str]
    selectors: Dict[str, str]
    is_active: Optional[bool] = True

class SourceCreate(SourceBase):
    pass

class SourceUpdate(BaseModel):
    name: Optional[str]
    url: Optional[str]
    description: Optional[str]
    selectors: Optional[Dict[str, str]]
    is_active: Optional[bool]

class SourceOut(SourceBase):
    id: UUID
    # created_at: datetime
    # updated_at: datetime

    class Config:
        from_attributes = True