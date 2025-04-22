from pydantic import BaseModel, HttpUrl
from uuid import UUID
from typing import Optional

class SourceBase(BaseModel):
    url: str  # Validate URL hợp lệ
    link_selector: str
    threads: int
    description: str
    card_information: str
    status: Optional[str] = "ACTIVE"  # Giá trị mặc định là "ACTIVE"

class SourceCreate(SourceBase):
    pass  # Kế thừa tất cả các trường từ SourceBase để tạo mới

class SourceUpdate(BaseModel):
    url: Optional[str] = None
    link_selector: Optional[str] = None
    threads: Optional[int] = None
    description: Optional[str] = None
    card_information: Optional[str] = None
    status: Optional[str] = None  # Các trường là tùy chọn để cập nhật

class SourceOut(SourceBase):
    id: UUID  # Thêm id để trả về thông tin đầy đủ

    class Config:
        from_attributes = True  # Cho phép chuyển đổi từ SQLAlchemy object sang Pydantic