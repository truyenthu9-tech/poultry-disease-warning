"""API xác thực."""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

import uuid

from app.api.deps import get_current_user, require_admin
from app.core.database import get_db
from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User
from app.models.enums import UserRole
from app.schemas.user import (
    AdminUserCreate, AdminUserUpdate, LoginRequest, Token, UserCreate,
    UserResponse, UserRoleUpdate, UserUpdate,
)

auth_router = APIRouter()


def _token(user: User) -> Token:
    return Token(
        access_token=create_access_token(str(user.id), user.role.value),
        user=UserResponse.model_validate(user),
    )


async def _active_admin_count(db: AsyncSession) -> int:
    return await db.scalar(
        select(func.count(User.id)).where(User.role == UserRole.ADMIN, User.is_active.is_(True))
    ) or 0


async def _ensure_admin_remains(db: AsyncSession, user: User, will_remain_admin: bool) -> None:
    if user.role == UserRole.ADMIN and user.is_active and not will_remain_admin:
        if await _active_admin_count(db) <= 1:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                "Không thể vô hiệu hóa, xóa hoặc hạ quyền quản trị viên cuối cùng",
            )


@auth_router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register(payload: UserCreate, db: AsyncSession = Depends(get_db)) -> Token:
    email = str(payload.email).strip().lower()
    exists = (await db.execute(select(User.id).where(func.lower(User.email) == email))).scalar_one_or_none()
    if exists:
        raise HTTPException(status.HTTP_409_CONFLICT, "Email đã tồn tại trong hệ thống")
    user = User(
        email=email,
        full_name=payload.full_name,
        password=hash_password(payload.password),
        role=UserRole.USER,  # đăng ký công khai luôn là người dùng thường
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return _token(user)


@auth_router.post("/login", response_model=Token)
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)) -> Token:
    email = payload.email.strip().lower()
    user = (await db.execute(select(User).where(func.lower(User.email) == email))).scalar_one_or_none()
    if user is None or not verify_password(payload.password, user.password):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Sai email hoặc mật khẩu")
    if not user.is_active:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Tài khoản đã bị vô hiệu hóa")
    user.last_login_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(user)
    return _token(user)


@auth_router.get("/me", response_model=UserResponse)
async def get_me(current: UserResponse = Depends(get_current_user)) -> UserResponse:
    return current


@auth_router.put("/me", response_model=UserResponse)
async def update_me(
    payload: UserUpdate,
    current: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    user = await db.get(User, current.id)
    if payload.full_name is not None:
        user.full_name = payload.full_name
    await db.commit()
    await db.refresh(user)
    return UserResponse.model_validate(user)


@auth_router.get("/users", response_model=list[UserResponse])
async def list_users(
    _: UserResponse = Depends(require_admin), db: AsyncSession = Depends(get_db)
) -> list[User]:
    """Admin xem danh sách tài khoản để cấp quyền."""
    return list((await db.execute(select(User).order_by(User.created_at))).scalars())


@auth_router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    payload: AdminUserCreate,
    _: UserResponse = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Admin tạo tài khoản user hoặc cán bộ thú y; admin mới chỉ được cấp riêng."""
    if payload.role == UserRole.ADMIN:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Không thể tạo quản trị viên từ màn hình này")
    email = str(payload.email).strip().lower()
    exists = (await db.execute(
        select(User.id).where(func.lower(User.email) == email)
    )).scalar_one_or_none()
    if exists:
        raise HTTPException(status.HTTP_409_CONFLICT, "Email đã tồn tại trong hệ thống")
    user = User(
        email=email,
        full_name=payload.full_name.strip(),
        password=hash_password(payload.password),
        role=payload.role,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@auth_router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: uuid.UUID,
    payload: AdminUserUpdate,
    current: UserResponse = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Admin cập nhật tên, email, vai trò và trạng thái tài khoản."""
    user = await db.get(User, user_id)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy tài khoản")

    if user_id == current.id:
        if payload.role is not None and payload.role != user.role:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Không thể tự đổi vai trò của chính mình")
        if payload.is_active is False:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Không thể tự vô hiệu hóa tài khoản")
    if payload.role == UserRole.ADMIN and user.role != UserRole.ADMIN:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Chỉ có thể tạo tài khoản người dùng hoặc cán bộ thú y")

    will_remain_admin = (payload.role or user.role) == UserRole.ADMIN and (
        payload.is_active if payload.is_active is not None else user.is_active
    )
    await _ensure_admin_remains(db, user, will_remain_admin)

    if payload.email is not None:
        email = str(payload.email).strip().lower()
        exists = (await db.execute(
            select(User.id).where(func.lower(User.email) == email, User.id != user_id)
        )).scalar_one_or_none()
        if exists:
            raise HTTPException(status.HTTP_409_CONFLICT, "Email đã được dùng bởi tài khoản khác")
        user.email = email
    if payload.full_name is not None:
        user.full_name = payload.full_name.strip()
    if payload.role is not None:
        user.role = payload.role
    if payload.is_active is not None:
        user.is_active = payload.is_active

    await db.commit()
    await db.refresh(user)
    return user


@auth_router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: uuid.UUID,
    current: UserResponse = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> Response:
    """Admin xóa tài khoản; dữ liệu trang trại và ổ dịch liên quan được giữ lại."""
    if user_id == current.id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Không thể xóa tài khoản đang đăng nhập")
    user = await db.get(User, user_id)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy tài khoản")
    await _ensure_admin_remains(db, user, will_remain_admin=False)
    await db.delete(user)
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@auth_router.put("/users/{user_id}/role", response_model=UserResponse)
async def update_user_role(
    user_id: uuid.UUID,
    payload: UserRoleUpdate,
    current: UserResponse = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    """Chỉ admin được đổi vai trò, và không tự đổi vai trò của chính mình."""
    if user_id == current.id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Không thể tự đổi vai trò của chính mình")
    user = await db.get(User, user_id)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy tài khoản")
    await _ensure_admin_remains(db, user, will_remain_admin=payload.role == UserRole.ADMIN)
    user.role = payload.role
    await db.commit()
    await db.refresh(user)
    return UserResponse.model_validate(user)


__all__ = ["auth_router"]
