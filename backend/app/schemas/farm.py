"""Schema liên quan đến trang trại chăn nuôi."""
from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


# Custom type enum for compatibility (not using SQLAlchemy ENUM for schemas)
class FarmTypeEnum(BaseModel):
    """Loại gia cầm - dùng cho validation schema."""

    BROILER = "broiler"
    LAYER = "layer"
    FREE_RANGE = "free_range"
    DUCK = "duck"
    GOOSE = "goose"
    TURKEY = "turkey"
    OTHER = "other"


class Location(BaseModel):
    """Tọa độ địa lý cho API request/response."""

    latitude: float = Field(gt=-90, lt=90)
    longitude: float = Field(gt=-180, lt=180)

    @field_validator("latitude", "longitude")
    @classmethod
    def validate_coords(cls, v):
        return v


class FarmCreate(BaseModel):
    """Dữ liệu tạo trang trại."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., min_length=1, max_length=255)
    owner_name: str = Field(..., min_length=1, max_length=255)
    phone: str = Field(..., min_length=8, max_length=20)
    email: str = Field(default=None)  # SPEC Section 3 yêu cầu field này, model chưa có FK constraint
    address: str = Field(..., max_length=65535)
    province: str = Field(..., min_length=1, max_length=100)
    district: Optional[str] = Field(default=None, max_length=100)
    latitude: float = Field(gt=-90, lt=90, alias="latitude")
    longitude: float = Field(gt=-180, lt=180, alias="longitude")
    poultry_type: str = Field(default="broiler", min_length=1, max_length=100)  # SPEC: String(100)
    capacity: int = Field(default=0, ge=0)
    is_active: bool = Field(default=True)  # SPEC Section 3 có field này (model cũng có)


class FarmUpdate(BaseModel):
    """Dữ liệu cập nhật trang trại."""

    model_config = ConfigDict(extra="forbid")

    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    owner_name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    phone: Optional[str] = Field(default=None, max_length=20)
    email: Optional[str] = Field(default=None)
    address: Optional[str] = Field(default=None, max_length=65535)
    province: Optional[str] = Field(default=None, max_length=100)
    district: Optional[str] = Field(default=None, max_length=100)
    latitude: Optional[float] = Field(default=None, gt=-90, lt=90)
    longitude: Optional[float] = Field(default=None, gt=-180, lt=180)
    poultry_type: Optional[str] = Field(default=None, min_length=1, max_length=100)
    capacity: Optional[int] = Field(default=None, ge=0)
    is_active: Optional[bool] = Field(default=None)
    notes: Optional[str] = Field(default=None, max_length=65535)


class FarmResponse(BaseModel):
    """Thông tin trang trại."""

    model_config = ConfigDict(from_attributes=True)

    id: str  # UUID string from model
    name: str
    owner_name: str
    phone: str
    email: Optional[str] = None  # SPEC Section 3 yêu cầu
    poultry_type: str
    capacity: int
    is_active: bool
    location: Location
    address: str
    province: str
    district: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None


__all__ = ["FarmCreate", "FarmUpdate", "FarmResponse", "Location", "FarmTypeEnum"]
