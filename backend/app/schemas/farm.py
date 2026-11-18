"""Schema trang trại."""
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.enums import PoultryType
from app.schemas.common import Location, ORMResponse

PHONE_PATTERN = r"^(0|\+84)\d{9}$"


class FarmCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=255)
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
    is_active: bool = True
    location: Location
    # Email của tài khoản được xem và xác nhận cảnh báo của trang trại này (chỉ cán bộ gán được)
    owner_user_email: EmailStr | None = None


class FarmUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=1, max_length=255)
    owner_name: str | None = Field(default=None, min_length=1, max_length=255)
    phone: str | None = Field(default=None, pattern=PHONE_PATTERN)
    email: EmailStr | None = None
    address: str | None = None
    province: str | None = Field(default=None, min_length=1, max_length=100)
    district: str | None = Field(default=None, max_length=100)
    commune: str | None = Field(default=None, max_length=100)
    hamlet: str | None = Field(default=None, max_length=150)
    poultry_type: PoultryType | None = None
    capacity: int | None = Field(default=None, ge=0)
    is_active: bool | None = None
    location: Location | None = None
    # Gửi null để bỏ liên kết tài khoản. Không gửi thì giữ nguyên.
    owner_user_email: EmailStr | None = None


class FarmResponse(ORMResponse):
    id: uuid.UUID
    name: str
    # Các trường liên hệ là None khi người xem không phải admin hoặc cán bộ thú y
    owner_name: str | None = None
    phone: str | None = None
    email: str | None = None
    address: str | None = None
    province: str
    district: str | None = None
    commune: str | None = None
    hamlet: str | None = None
    poultry_type: PoultryType
    capacity: int
    is_active: bool
    # Chỉ admin và cán bộ thú y thấy tài khoản sở hữu
    owner_user_id: uuid.UUID | None = None
    location: Location | None = None
    created_at: datetime
    updated_at: datetime


class FarmNearby(BaseModel):
    farm: FarmResponse
    distance_km: float


__all__ = ["FarmCreate", "FarmUpdate", "FarmResponse", "FarmNearby", "Location"]
