"""Schema cho hồ sơ đăng ký trại chờ duyệt."""
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.models.enums import FarmRegistrationStatus, PoultryType
from app.schemas.common import Location, ORMResponse
from app.schemas.farm import PHONE_PATTERN


class FarmRegistrationCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    farm_name: str = Field(min_length=1, max_length=255)
    owner_name: str = Field(min_length=1, max_length=255)
    phone: str = Field(pattern=PHONE_PATTERN)
    email: EmailStr | None = None
    address: str | None = None
    province: str = Field(min_length=1, max_length=100)
    district: str | None = Field(default=None, max_length=100)
    commune: str | None = Field(default=None, max_length=100)
    hamlet: str | None = Field(default=None, max_length=150)
    poultry_type: PoultryType = PoultryType.CHICKEN
    capacity: int = Field(default=0, ge=0)
    location: Location

    @field_validator("farm_name", "owner_name", "province", mode="before")
    @classmethod
    def strip_required_text(cls, value):
        return value.strip() if isinstance(value, str) else value


class FarmRegistrationReject(BaseModel):
    model_config = ConfigDict(extra="forbid")

    review_note: str = Field(min_length=1, max_length=2000)

    @field_validator("review_note", mode="before")
    @classmethod
    def strip_note(cls, value):
        return value.strip() if isinstance(value, str) else value


class FarmRegistrationResponse(ORMResponse):
    id: uuid.UUID
    submitted_by_id: uuid.UUID
    status: FarmRegistrationStatus

    farm_name: str
    owner_name: str
    phone: str
    email: str | None = None
    address: str | None = None
    province: str
    district: str | None = None
    commune: str | None = None
    hamlet: str | None = None
    poultry_type: PoultryType
    capacity: int
    location: Location

    virus_type: str | None = None
    disease_started_at: datetime | None = None
    cases_count: int | None = None
    disease_description: str | None = None

    reviewed_by_id: uuid.UUID | None = None
    reviewed_at: datetime | None = None
    review_note: str | None = None
    farm_id: uuid.UUID | None = None
    outbreak_id: uuid.UUID | None = None
    created_at: datetime
    updated_at: datetime


__all__ = ["FarmRegistrationCreate", "FarmRegistrationReject", "FarmRegistrationResponse"]
