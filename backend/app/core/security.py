"""Xử lý mã hóa mật khẩu, tạo/kiểm tra JWT và middleware bảo vệ route có token."""

import os
import secrets
from datetime import datetime, timezone
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.user import User, UserRole

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

ALGORITHM = settings.jwt_algorithm
TOKEN_EXPIRE_MINUTES = settings.jwt_token_expire_minutes


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(subject: str, role: UserRole = UserRole.FARMER) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": subject,
        "role": role.value,
        "exp": now + timezone.timedelta(minutes=TOKEN_EXPIRE_MINUTES),
    }
    return jwt.encode(
        payload,
        key=settings.jwt_secret_key,
        algorithm=ALGORITHM,
    )


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Đóng vai trò dependency: kiểm tra token rồi trả về User (nâng 401 nếu lỗi)."""
    if not token:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[ALGORITHM])
        subject: str = payload.get("sub")
        role: UserRole = UserRole(payload.get("role", ""))
    except (JWTError, ValueError, TypeError):
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired JWT token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if role not in UserRole.__members__:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Unknown role")

    user = (await db.execute(select(User).where(User.username == subject))).scalar_one()
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="User not found")
    if not user.is_active:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Account is disabled")
    return user