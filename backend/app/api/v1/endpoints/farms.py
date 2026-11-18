"""API quản lý trang trại."""
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_staff
from app.api.privacy import farm_view
from app.core.database import get_db
from app.models.enums import PoultryType
from app.models.farm import Farm
from app.models.user import User
from app.schemas.farm import FarmCreate, FarmResponse, FarmUpdate
from app.schemas.user import UserResponse
from app.utils.geo import location_to_geometry

farm_router = APIRouter(prefix="/farms")


async def _get_or_404(db: AsyncSession, farm_id: uuid.UUID) -> Farm:
    farm = await db.get(Farm, farm_id)
    if farm is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy trang trại")
    return farm


async def _resolve_owner_id(db: AsyncSession, email: str | None) -> uuid.UUID | None:
    """Tìm tài khoản theo email để gán làm chủ trang trại. None nghĩa là không gán tài khoản nào."""
    if email is None:
        return None
    user = (
        await db.execute(select(User).where(func.lower(User.email) == email.lower()))
    ).scalar_one_or_none()
    if user is None or not user.is_active:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy tài khoản có email này")
    return user.id


@farm_router.post(
    "", response_model=FarmResponse, status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_staff)],
)
async def create_farm(payload: FarmCreate, db: AsyncSession = Depends(get_db)):
    data = payload.model_dump(exclude={"location", "owner_user_email"})
    farm = Farm(
        **data,
        owner_user_id=await _resolve_owner_id(db, payload.owner_user_email),
        location=location_to_geometry(payload.location.latitude, payload.location.longitude),
    )
    db.add(farm)
    await db.commit()
    await db.refresh(farm)
    return farm


@farm_router.get("", response_model=list[FarmResponse])
async def list_farms(
    province: str | None = None,
    district: str | None = None,
    poultry_type: PoultryType | None = None,
    is_active: bool | None = None,
    mine: bool = False,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current: UserResponse = Depends(get_current_user),
):
    stmt = select(Farm)
    if mine:
        stmt = stmt.where(Farm.owner_user_id == current.id)
    if province:
        stmt = stmt.where(Farm.province == province)
    if district:
        stmt = stmt.where(Farm.district == district)
    if poultry_type:
        stmt = stmt.where(Farm.poultry_type == poultry_type)
    if is_active is not None:
        stmt = stmt.where(Farm.is_active == is_active)
    stmt = stmt.order_by(Farm.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    return [farm_view(f, current) for f in (await db.execute(stmt)).scalars()]


@farm_router.get("/{farm_id}", response_model=FarmResponse)
async def get_farm(
    farm_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current: UserResponse = Depends(get_current_user),
):
    return farm_view(await _get_or_404(db, farm_id), current)


@farm_router.put("/{farm_id}", response_model=FarmResponse, dependencies=[Depends(require_staff)])
async def update_farm(farm_id: uuid.UUID, payload: FarmUpdate, db: AsyncSession = Depends(get_db)):
    farm = await _get_or_404(db, farm_id)
    data = payload.model_dump(exclude_unset=True, exclude={"location", "owner_user_email"})
    for key, value in data.items():
        setattr(farm, key, value)
    if "owner_user_email" in payload.model_fields_set:
        farm.owner_user_id = await _resolve_owner_id(db, payload.owner_user_email)
    if payload.location is not None:
        farm.location = location_to_geometry(payload.location.latitude, payload.location.longitude)
    await db.commit()
    await db.refresh(farm)
    return farm


@farm_router.delete(
    "/{farm_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_staff)]
)
async def delete_farm(farm_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    farm = await _get_or_404(db, farm_id)
    await db.delete(farm)
    await db.commit()


__all__ = ["farm_router"]
