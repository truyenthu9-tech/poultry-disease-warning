"""Schema tài khoản."""
import uuid

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.models.enums import UserRole


class UserCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: EmailStr
    full_name: str = Field(min_length=2, max_length=255)
    password: str = Field(min_length=8, max_length=128)


class UserUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    full_name: str | None = Field(default=None, min_length=2, max_length=255)


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: EmailStr
    full_name: str
    role: UserRole
    is_active: bool


class UserRoleUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role: UserRole


class AdminUserCreate(BaseModel):
    """Tạo tài khoản thường hoặc cán bộ thú y từ màn hình quản trị."""
    model_config = ConfigDict(extra="forbid")

    email: EmailStr
    full_name: str = Field(min_length=2, max_length=255)
    password: str = Field(min_length=8, max_length=128)
    role: UserRole = UserRole.USER

    @field_validator("full_name", mode="before")
    @classmethod
    def normalize_full_name(cls, value):
        return value.strip() if isinstance(value, str) else value


class AdminUserUpdate(BaseModel):
    """Thông tin tài khoản chỉ quản trị viên được phép sửa."""
    model_config = ConfigDict(extra="forbid")

    email: EmailStr | None = None
    full_name: str | None = Field(default=None, min_length=2, max_length=255)
    role: UserRole | None = None
    is_active: bool | None = None

    @field_validator("full_name", mode="before")
    @classmethod
    def normalize_full_name(cls, value):
        return value.strip() if isinstance(value, str) else value


class LoginRequest(BaseModel):
    email: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


__all__ = ["UserCreate", "UserUpdate", "UserRoleUpdate", "AdminUserCreate", "AdminUserUpdate", "UserResponse", "LoginRequest", "Token"]
