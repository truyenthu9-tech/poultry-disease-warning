"""Schema báo cáo dịch riêng chờ cán bộ thú y xác nhận."""
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.common import Location, ORMResponse
from app.schemas.farm import PHONE_PATTERN


class OutbreakReportCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reporter_name: str = Field(min_length=1, max_length=255)
    phone: str = Field(pattern=PHONE_PATTERN)
    virus_type: str = Field(min_length=1, max_length=255)
    province: str = Field(min_length=1, max_length=100)
    district: str | None = Field(default=None, max_length=100)
    commune: str | None = Field(default=None, max_length=100)
    hamlet: str | None = Field(default=None, max_length=150)
    address: str | None = None
    location: Location
    onset_date: datetime
    cases_count: int = Field(ge=1)
    description: str | None = None

    @field_validator("reporter_name", "virus_type", "province", mode="before")
    @classmethod
    def strip_required_text(cls, value):
        return value.strip() if isinstance(value, str) else value

    @field_validator("onset_date")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("Thời điểm phát bệnh cần có múi giờ")
        return value


class OutbreakReportReject(BaseModel):
    model_config = ConfigDict(extra="forbid")

    review_note: str = Field(min_length=1, max_length=2000)

    @field_validator("review_note", mode="before")
    @classmethod
    def strip_note(cls, value):
        return value.strip() if isinstance(value, str) else value


class OutbreakReportResponse(ORMResponse):
    id: uuid.UUID
    submitted_by_id: uuid.UUID
    status: str
    reporter_name: str
    phone: str
    virus_type: str
    province: str
    district: str | None = None
    commune: str | None = None
    hamlet: str | None = None
    address: str | None = None
    location: Location
    onset_date: datetime
    cases_count: int
    description: str | None = None
    reviewed_by_id: uuid.UUID | None = None
    reviewed_at: datetime | None = None
    review_note: str | None = None
    outbreak_id: uuid.UUID | None = None
    created_at: datetime
    updated_at: datetime


__all__ = ["OutbreakReportCreate", "OutbreakReportReject", "OutbreakReportResponse"]
