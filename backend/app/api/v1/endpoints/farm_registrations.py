"""Đăng ký trang trại kèm báo cáo dịch và chờ cán bộ thú y xét duyệt."""
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_staff
from app.core.database import get_db
from app.models.enums import FarmRegistrationStatus
from app.models.farm import Farm
from app.models.farm_registration import FarmRegistration
from app.models.user import User
from app.schemas.farm_registration import (
    FarmRegistrationCreate,
    FarmRegistrationReject,
    FarmRegistrationResponse,
)
from app.schemas.user import UserResponse
from app.utils.geo import location_to_geometry

farm_registration_router = APIRouter(prefix="/farm-registrations")


async def _get_for_review(db: AsyncSession, registration_id: uuid.UUID) -> FarmRegistration:
    registration = await db.scalar(
        select(FarmRegistration)
        .where(FarmRegistration.id == registration_id)
        .with_for_update()
    )
    if registration is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy hồ sơ đăng ký")
    if registration.status != FarmRegistrationStatus.PENDING.value:
        raise HTTPException(status.HTTP_409_CONFLICT, "Hồ sơ này đã được xử lý")
    return registration


@farm_registration_router.post(
    "", response_model=FarmRegistrationResponse, status_code=status.HTTP_201_CREATED
)
async def submit_farm_registration(
    payload: FarmRegistrationCreate,
    db: AsyncSession = Depends(get_db),
    current: UserResponse = Depends(get_current_user),
):
    """Lưu hồ sơ đăng ký riêng tư; chưa tạo trang trại đến khi cán bộ chấp thuận."""
    data = payload.model_dump(exclude={"location", "email"})
    registration = FarmRegistration(
        **data,
        email=str(payload.email) if payload.email else current.email,
        submitted_by_id=current.id,
        location=location_to_geometry(payload.location.latitude, payload.location.longitude),
        status=FarmRegistrationStatus.PENDING.value,
    )
    db.add(registration)
    await db.commit()
    await db.refresh(registration)
    return registration


@farm_registration_router.get("/mine", response_model=list[FarmRegistrationResponse])
async def list_my_farm_registrations(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current: UserResponse = Depends(get_current_user),
):
    stmt = (
        select(FarmRegistration)
        .where(FarmRegistration.submitted_by_id == current.id)
        .order_by(FarmRegistration.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    return list((await db.execute(stmt)).scalars())


@farm_registration_router.get(
    "", response_model=list[FarmRegistrationResponse], dependencies=[Depends(require_staff)]
)
async def list_farm_registrations(
    status_: FarmRegistrationStatus | None = Query(default=FarmRegistrationStatus.PENDING, alias="status"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(FarmRegistration)
    if status_ is not None:
        stmt = stmt.where(FarmRegistration.status == status_.value)
    stmt = stmt.order_by(FarmRegistration.created_at.asc()).offset((page - 1) * page_size).limit(page_size)
    return list((await db.execute(stmt)).scalars())


@farm_registration_router.post(
    "/{registration_id}/approve", response_model=FarmRegistrationResponse
)
async def approve_farm_registration(
    registration_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current: UserResponse = Depends(require_staff),
):
    """Chấp thuận hồ sơ và tạo trang trại trong một giao dịch."""
    registration = await _get_for_review(db, registration_id)
    now = datetime.now(timezone.utc)

    farm = Farm(
        name=registration.farm_name,
        owner_name=registration.owner_name,
        phone=registration.phone,
        email=registration.email,
        address=registration.address,
        province=registration.province,
        district=registration.district,
        commune=registration.commune,
        hamlet=registration.hamlet,
        poultry_type=registration.poultry_type,
        capacity=registration.capacity,
        is_active=True,
        owner_user_id=registration.submitted_by_id,
        location=registration.location,
    )
    db.add(farm)
    await db.flush()

    registration.status = FarmRegistrationStatus.APPROVED.value
    registration.reviewed_by_id = current.id
    registration.reviewed_at = now
    registration.farm_id = farm.id
    await db.commit()
    await db.refresh(registration)
    return registration


@farm_registration_router.post(
    "/{registration_id}/reject", response_model=FarmRegistrationResponse
)
async def reject_farm_registration(
    registration_id: uuid.UUID,
    payload: FarmRegistrationReject,
    db: AsyncSession = Depends(get_db),
    current: UserResponse = Depends(require_staff),
):
    """Từ chối hồ sơ và lưu lý do để người gửi xem được."""
    registration = await _get_for_review(db, registration_id)
    registration.status = FarmRegistrationStatus.REJECTED.value
    registration.reviewed_by_id = current.id
    registration.reviewed_at = datetime.now(timezone.utc)
    registration.review_note = payload.review_note
    await db.commit()
    await db.refresh(registration)
    return registration


__all__ = ["farm_registration_router"]
