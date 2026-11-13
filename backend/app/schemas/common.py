"""Chung cho các schema Pydantic."""
from datetime import datetime
from typing import List, Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field


class Location(BaseModel):
    """Tọa độ địa lý cho API request/response.
    
    Định dạng: JSON {"latitude": float, "longitude": float}
    GeoAlchemy2 sẽ chuyển đổi từ/to WKB trong model layer.
    """

    latitude: float = Field(gt=-90, lt=90)
    longitude: float = Field(gt=-180, lt=180)


class BaseResponse(BaseModel):
    """Cấu trúc phản hồi chung."""

    success: bool = True
    message: str = "Thành công"
    data: dict | None = None


class BaseSchema(BaseModel):
    """Cấu hình chung cho mọi schema."""

    model_config = ConfigDict(from_attributes=True)


T = TypeVar('T')


class PageList(BaseModel, Generic[T]):
    """Danh sách có pagination (cho Response)."""

    items: List[T]
    total: int
    page: int
    per_page: int


class PaginationParams(BaseModel):
    """Param cho phân trang."""

    page: int = Field(default=1, ge=1)
    per_page: int = Field(default=10, ge=1, le=100)


class TimeBase(BaseModel):
    """Trường thời gian chung."""

    created_at: datetime
    updated_at: datetime | None = None


__all__ = [
    "Location",
    "BaseResponse", 
    "BaseSchema",
    "PageList",
    "PaginationParams",
    "TimeBase",
]
