# from pydantic import BaseModel, UUID4
# from datetime import datetime
# from typing import Dict, Any

# # Schema cơ bản chứa các trường chung
# class ResultBase(BaseModel):
#     url: str
#     contents: Dict[str, Any]  # contents là một dictionary với key-value bất kỳ
#     time_stamp: datetime

# # Schema dùng để tạo mới một Result
# class ResultCreate(ResultBase):
#     source_id: UUID4

# # Schema dùng để trả về dữ liệu Result từ database
# class Result(ResultBase):
#     id: UUID4
#     source_id: UUID4

#     class Config:
#         orm_mode = True  # Cho phép chuyển đổi từ SQLAlchemy model sang Pydantic


from pydantic import BaseModel, UUID4, HttpUrl, ConfigDict, Field
from datetime import datetime
from typing import Dict, Any

class ResultBase(BaseModel):
    url: str = Field(..., max_length=500)  # Changed from HttpUrl to str
    contents: Dict[str, Any] = Field(
        ...,
        description="JSON content extracted from the webpage"
    )
    time_stamp: datetime = Field(default_factory=datetime.now)

class ResultCreate(ResultBase):
    source_id: UUID4 = Field(..., description="ID of the source website")

class Result(ResultBase):
    id: UUID4 = Field(..., description="Unique identifier for the result")
    source_id: UUID4

    model_config = ConfigDict(
        from_attributes=True
    )