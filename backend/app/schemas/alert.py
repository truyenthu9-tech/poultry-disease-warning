"""Schema liên quan đến cảnh báo."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class Location(BaseModel):
    """Tọa độ địa lý cho API request/response."""

    latitude: float = Field(gt=-90, lt=90)
    longitude: float = Field(gt=-180, lt=180)

    @classmethod
    def validate_coords(cls, v):
        return v


class AlertCreate(BaseModel):
    """Dữ liệu tạo cảnh báo."""

    model_config = ConfigDict(extra="forbid")

    outbreak_id: str
    farm_id: Optional[str] = None
    risk_level: str = Field(default="medium", pattern=r"^(low|medium|high|very_high)$")
    message: str = Field(..., min_length=2, max_length=65535)


class AlertUpdate(BaseModel):
    """Dữ liệu cập nhật cảnh báo."""

    model_config = ConfigDict(extra="forbid")

    risk_level: Optional[str] = Field(default=None, pattern=r"^(low|medium|high|very_high)$")
    message: Optional[str] = Field(default=None, max_length=65535)
    status: Optional[str] = Field(default=None)


class AlertResponse(BaseModel):
    """Thông tin cảnh báo."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    risk_level: str
    message: str
    status: str
    triggered_at: datetime | None = None
    outbreak_id: str
    farm_id: Optional[str] = None
    distance_km: float = 0.0


__all__ = ["AlertCreate", "AlertUpdate", "AlertResponse", "Location"]
