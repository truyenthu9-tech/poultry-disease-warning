"""Model người dùng / tài khoản."""
from datetime import datetime, timezone
from enum import Enum as PyEnum
import uuid
from sqlalchemy import CHAR, DateTime, String, Text, func
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, BaseModel
from app.core.config import settings
from app.models.enums import UserRole


class User(BaseModel):
    """Tài khoản người dùng."""

    __tablename__ = "users"

    email: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False
    )
    """Địa chỉ email đăng nhập."""

    password: Mapped[str] = mapped_column(
        CHAR(settings.PASSWORD_LENGTH, nullable=False), index=True
    )
    """Hash mật khẩu (bcrypt)."""

    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    """Tên đầy đủ."""

    role: Mapped[UserRole] = mapped_column(
        ENUM(UserRole, name="user_role"), default=UserRole.USER, index=True, nullable=False
    )
    """Vai trò: admin, user, vet_officer, farm_owner."""

    is_active: Mapped[bool] = mapped_column(
        bool, default=True, server_default="true", nullable=False
    )
    """Chưa bị vô hiệu hóa."""

    last_login_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    """Thời điểm đăng nhập gần nhất."""

    farm: Mapped["Farm"] | None = (
        relationship("Farm", back_populates="owner", uselist=False)
    )
    """Farm đang quản lý (nếu có)."""


__all__ = ["User", "UserRole"]
