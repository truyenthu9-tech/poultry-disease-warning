"""Schema liên quan đến tài khoản người dùng."""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.core.config import settings
from app.models.user import UserRole


class UserCreate(BaseModel):
    """Dữ liệu tạo tài khoản."""

    model_config = ConfigDict(extra="forbid")

    email: EmailStr
    full_name: str = Field(min_length=2, max_length=255)
    password: str = Field(min_length=8, max_length=128)
    role: UserRole = UserRole.USER


class UserUpdate(BaseModel):
    """Dữ liệu cập nhật tài khoản."""

    model_config = ConfigDict(extra="forbid")

    full_name: str | None = Field(default=None, min_length=2, max_length=255)
    role: UserRole | None = Field(default=None)
    is_active: bool | None = Field(default=None)


class UserResponse(BaseModel):
    """Thông tin tài khoản (không trả mật khẩu)."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    email: EmailStr
    full_name: str
    role: UserRole
    is_active: bool
    farm_id: str | None = None


class Token(BaseModel):
    """Phản hồi xác thực."""

    access_token: str
    token_type: str = "bearer"
    user: UserResponse


__all__ = ["UserCreate", "UserUpdate", "UserResponse", "Token"]