from pydantic import BaseModel
from uuid import UUID
from typing import Optional

class AttributeBase(BaseModel):
    name: str
    type: str
    description: str
    source_id: UUID  # Khóa ngoại liên kết với sources.id

class AttributeCreate(AttributeBase):
    pass  # Kế thừa tất cả để tạo mới

class AttributeUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None
    description: Optional[str] = None
    source_id: Optional[UUID] = None  # Các trường là tùy chọn để cập nhật

class AttributeOut(AttributeBase):
    id: UUID  # Thêm id để trả về thông tin đầy đủ

    class Config:
        from_attributes = True