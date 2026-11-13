"""Phụ thuộc chung cho các route API."""
from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import UserRole

from .schemas.user import UserResponse


async def get_current_user(
    db: Session = Depends(get_db),
    x_user_id: str | None = None,
) -> UserResponse:
    """Lấy tài khoản hiện tại từ header X-User-Id."""

    if not x_user_id:
        raise RuntimeError("Missing user id")

    from app.models.user import User

    user = db.get(User, x_user_id)
    if user is None:
        raise RuntimeError("User not found")

    return UserResponse.model_validate(user)


__all__ = ["get_db", "get_current_user"]