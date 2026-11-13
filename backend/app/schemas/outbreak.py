"""Schema liên quan đến ổ dịch gia cầm."""
from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class Location(BaseModel):
    """Tọa độ địa lý cho API request/response."""

    latitude: float = Field(gt=-90, lt=90)
    longitude: float = Field(gt=-180, lt=180)


class OutbreakCreate(BaseModel):
    """Dữ liệu tạo ổ dịch."""

    model_config = ConfigDict(extra="forbid")

    virus_type: str = Field(..., min_length=1, max_length=255)
    province: str = Field(..., min_length=1, max_length=100)
    district: Optional[str] = Field(default=None, max_length=100)
    latitude: float = Field(gt=-90, lt=90, alias="latitude")
    longitude: float = Field(gt=-180, lt=180, alias="longitude")
    address: str = Field(..., max_length=65535)
    cases_count: int = Field(default=0, ge=0)
    severity: str = Field(default="medium", min_length=1, max_length=20)
    reported_date: Optional[datetime] = Field(default=None)


class OutbreakUpdate(BaseModel):
    """Dữ liệu cập nhật ổ dịch."""

    model_config = ConfigDict(extra="forbid")

    virus_type: Optional[str] = Field(default=None, min_length=1, max_length=255)
    province: Optional[str] = Field(default=None, max_length=100)
    district: Optional[str] = Field(default=None, max_length=100)
    latitude: Optional[float] = Field(default=None, gt=-90, lt=90)
    longitude: Optional[float] = Field(default=None, gt=-180, lt=180)
    address: Optional[str] = Field(default=None, max_length=65535)
    cases_count: Optional[int] = Field(default=None, ge=0)
    severity: Optional[str] = Field(default=None, min_length=1, max_length=20)
    status: Optional[str] = Field(default=None)


class OutbreakResponse(BaseModel):
    """Thông tin ổ dịch."""

    model_config = ConfigDict(from_attributes=True)

    id: str  # UUID string from model (not auto-generated in schema since model uses String id)
    virus_type: str
    province: str
    district: Optional[str] = None
    location: Location
    address: str
    cases_count: int
    status: str  # ENUM value from model (pending, active, resolved, etc.)
    severity: str
    reported_date: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


__all__ = ["OutbreakCreate", "OutbreakUpdate", "OutbreakResponse", "Location"]
