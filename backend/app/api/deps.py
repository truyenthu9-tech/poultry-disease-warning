"""Dependency dùng chung cho các route: xác thực và phân quyền."""
import uuid

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.user import UserResponse

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

# Vai trò được ghi dữ liệu và xem thông tin liên hệ đầy đủ của trang trại
STAFF_ROLES = frozenset({UserRole.ADMIN, UserRole.VET_OFFICER})


def is_staff(user: UserResponse) -> bool:
    return user.role in STAFF_ROLES


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    credentials_error = HTTPException(
        status.HTTP_401_UNAUTHORIZED,
        "Token không hợp lệ hoặc đã hết hạn",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_access_token(token)
        user_id = uuid.UUID(payload["sub"])
    except (jwt.PyJWTError, KeyError, ValueError):
        raise credentials_error

    user = await db.get(User, user_id)
    if user is None or not user.is_active:
        raise credentials_error
    return UserResponse.model_validate(user)


async def require_staff(current: UserResponse = Depends(get_current_user)) -> UserResponse:
    """Chỉ quản trị viên và cán bộ thú y."""
    if not is_staff(current):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Bạn không có quyền thực hiện thao tác này")
    return current


async def require_admin(current: UserResponse = Depends(get_current_user)) -> UserResponse:
    """Chỉ quản trị viên."""
    if current.role != UserRole.ADMIN:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Chỉ quản trị viên mới có quyền này")
    return current


__all__ = ["get_db", "get_current_user", "require_staff", "require_admin", "is_staff", "STAFF_ROLES"]
