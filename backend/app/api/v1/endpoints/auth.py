"""Router API xác thực tài khoản."""
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import EmailStr, ValidationError, BaseModel
from passlib.context import CryptContext
from typing import Union

from app.api.deps import get_current_user
from app.schemas.user import Token, UserCreate, UserResponse, UserUpdate
from app.core.config import settings
from app.core.database import get_db
from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User, UserRole

from sqlalchemy.orm import Session

router = APIRouter(prefix="/auth", tags=["auth"])

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
def register(
    payload: UserCreate,
    db: Session = Depends(get_db),
) -> Token:
    """Đăng ký tài khoản mới."""
    if not payload.email or not payload.full_name or not payload.password:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "Email, tên và mật khẩu bắt buộc"
        )

    # Check if email already exists
    existing_user = db.query(User).filter(User.email == payload.email).first()
    if existing_user:
        raise HTTPException(
            status.HTTP_409_CONFLICT, "Email đã tồn tại trong hệ thống"
        )

    user = User(
        email=payload.email,
        full_name=payload.full_name,
        password=hash_password(payload.password),
        role=payload.role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return _login(db, user.email, user)


class Login(BaseModel):
    """Dữ liệu đăng nhập."""
    email: EmailStr
    password: str


@router.post("/login", response_model=Token)
def login(
    payload: Login,
    db: Session = Depends(get_db),
) -> Token:
    """Đăng nhập và trả token truy cập."""
    user = db.query(User).filter(User.email == payload.email).first()
    
    if not user or not verify_password(payload.password, user.password):
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED, "Sai email hoặc mật khẩu"
        )

    if not user.is_active:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN, "Tài khoản đã bị vô hiệu hóa"
        )

    # Update last login time
    from sqlalchemy import func
    db.query(User).filter(User.email == payload.email).update({"last_login_at": func.now()})
    db.commit()

    return _login(db, user.email, user)


@router.get("/me", response_model=UserResponse)
def get_me(
    x_user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserResponse:
    """Lấy thông tin tài khoản hiện tại."""
    return UserResponse.model_validate(db.get(User, x_user_id))


@router.put("/me", response_model=UserResponse)
def update_me(
    payload: UserUpdate,
    x_user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserResponse:
    """Cập nhật thông tin tài khoản hiện tại."""
    user = db.get(User, x_user_id)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy tài khoản")

    if payload.full_name is not None:
        if not payload.full_name or len(payload.full_name) < 2:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST, "Tên không hợp lệ"
            )
        user.full_name = payload.full_name

    if payload.role is not None:
        user.role = payload.role

    if payload.is_active is not None:
        user.is_active = payload.is_active

    db.commit()
    db.refresh(user)
    return UserResponse.model_validate(user)


def _login(db: Session, email: str, user: User) -> Token:
    """Tạo token truy cập cho người dùng."""
    from app.core.config import settings

    access_token = create_access_token(
        subject=str(user.id),
        expires_delta=timedelta(
            minutes=int(settings.ACCESS_TOKEN_MINUTES), seconds=30
        ),
    )
    return Token(
        access_token=access_token,
        user=UserResponse.model_validate(user),
    )


__all__ = ["router"]