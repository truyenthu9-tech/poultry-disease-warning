"""Schema ổ dịch."""
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import OutbreakStatus, Severity
from app.schemas.common import Location, ORMResponse


class OutbreakCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    virus_type: str = Field(min_length=1, max_length=255)
    province: str = Field(min_length=1, max_length=100)
    district: str | None = Field(default=None, max_length=100)
    commune: str | None = Field(default=None, max_length=100)
    hamlet: str | None = Field(default=None, max_length=150)
    address: str | None = None
    location: Location
    cases_count: int = Field(default=0, ge=0)
    status: OutbreakStatus = OutbreakStatus.ACTIVE
    severity: Severity = Severity.MEDIUM
    radius_km: float | None = Field(default=None, gt=0, le=500)
    reported_date: datetime | None = None
    onset_date: datetime | None = None


class OutbreakUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    virus_type: str | None = Field(default=None, min_length=1, max_length=255)
    province: str | None = Field(default=None, min_length=1, max_length=100)
    district: str | None = Field(default=None, max_length=100)
    commune: str | None = Field(default=None, max_length=100)
    hamlet: str | None = Field(default=None, max_length=150)
    address: str | None = None
    location: Location | None = None
    cases_count: int | None = Field(default=None, ge=0)
    status: OutbreakStatus | None = None
    severity: Severity | None = None
    radius_km: float | None = Field(default=None, gt=0, le=500)
    reported_date: datetime | None = None
    onset_date: datetime | None = None


class OutbreakResponse(ORMResponse):
    id: uuid.UUID
    virus_type: str
    province: str
    district: str | None = None
    commune: str | None = None
    hamlet: str | None = None
    address: str | None = None
    location: Location | None = None
    cases_count: int
    status: OutbreakStatus
    severity: Severity
    radius_km: float
    reported_date: datetime
    onset_date: datetime | None = None
    source: str
    source_url: str | None = None
    verified: bool
    verified_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class OutbreakImportResult(BaseModel):
    """Kết quả một lần nhập dữ liệu ổ dịch từ nguồn bên ngoài."""

    sources_configured: int
    fetched: int
    created: int
    duplicates: int
    invalid: int
    errors: list[str] = []


__all__ = ["OutbreakCreate", "OutbreakUpdate", "OutbreakResponse", "OutbreakImportResult", "Location"]
