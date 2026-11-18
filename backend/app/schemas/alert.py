"""Schema cảnh báo."""
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import AlertStatus, RiskLevel
from app.schemas.common import Location


class AlertCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    outbreak_id: uuid.UUID
    farm_id: uuid.UUID
    risk_level: RiskLevel = RiskLevel.MEDIUM
    message: str = Field(min_length=2)


class AlertUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    risk_level: RiskLevel | None = None
    message: str | None = Field(default=None, min_length=2)
    status: AlertStatus | None = None


class AlertResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    outbreak_id: uuid.UUID
    farm_id: uuid.UUID
    distance_km: float
    risk_level: RiskLevel
    message: str
    risk_basis: str | None = None
    status: AlertStatus
    sent_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


__all__ = ["AlertCreate", "AlertUpdate", "AlertResponse", "Location"]
