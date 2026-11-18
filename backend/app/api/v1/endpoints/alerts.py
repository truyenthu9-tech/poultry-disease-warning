"""API quản lý cảnh báo."""
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, is_staff, require_staff
from app.core.database import get_db
from app.models.alert import Alert
from app.models.enums import AlertStatus, RiskLevel
from app.models.farm import Farm
from app.models.outbreak import Outbreak
from app.schemas.alert import AlertCreate, AlertResponse, AlertUpdate
from app.schemas.user import UserResponse
from app.services.alert_service import generate_alerts_for_outbreak
from app.services.spatial_service import find_farms_within_radius
from app.utils.geo import geometry_to_location

alert_router = APIRouter(prefix="/alerts")


async def _get_or_404(db: AsyncSession, alert_id: uuid.UUID) -> Alert:
    alert = await db.get(Alert, alert_id)
    if alert is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy cảnh báo")
    return alert


async def _get_visible_or_404(db: AsyncSession, alert_id: uuid.UUID, current: UserResponse) -> Alert:
    """Lấy cảnh báo mà người dùng được phép thấy.

    Admin và cán bộ thú y thấy mọi cảnh báo. Người dùng khác chỉ thấy cảnh báo của trang trại
    do tài khoản mình sở hữu. Cảnh báo của trang trại khác trả 404 giống cảnh báo không tồn tại,
    để không lộ việc nó có tồn tại.
    """
    stmt = select(Alert).where(Alert.id == alert_id)
    if not is_staff(current):
        stmt = stmt.join(Farm, Farm.id == Alert.farm_id).where(Farm.owner_user_id == current.id)
    alert = (await db.execute(stmt)).scalar_one_or_none()
    if alert is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy cảnh báo")
    return alert


def _require_verified(outbreak: Outbreak) -> None:
    if outbreak.verified is False:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "Ổ dịch chưa được cán bộ thú y xác nhận nên chưa thể tạo cảnh báo",
        )


@alert_router.post(
    "/outbreaks/{outbreak_id}/generate",
    response_model=list[AlertResponse],
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_staff)],
)
async def generate_alerts(outbreak_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    outbreak = await db.get(Outbreak, outbreak_id)
    if outbreak is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy ổ dịch")
    _require_verified(outbreak)
    return await generate_alerts_for_outbreak(db, outbreak)


@alert_router.get("", response_model=list[AlertResponse])
async def list_alerts(
    farm_id: uuid.UUID | None = None,
    outbreak_id: uuid.UUID | None = None,
    status_: AlertStatus | None = Query(default=None, alias="status"),
    risk_level: RiskLevel | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current: UserResponse = Depends(get_current_user),
):
    stmt = select(Alert)
    if not is_staff(current):
        # Người dùng thường chỉ thấy cảnh báo của trang trại do tài khoản mình sở hữu
        stmt = stmt.join(Farm, Farm.id == Alert.farm_id).where(Farm.owner_user_id == current.id)
    if farm_id:
        stmt = stmt.where(Alert.farm_id == farm_id)
    if outbreak_id:
        stmt = stmt.where(Alert.outbreak_id == outbreak_id)
    if status_:
        stmt = stmt.where(Alert.status == status_)
    if risk_level:
        stmt = stmt.where(Alert.risk_level == risk_level)
    stmt = stmt.order_by(Alert.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    return list((await db.execute(stmt)).scalars())


@alert_router.post(
    "", response_model=AlertResponse, status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_staff)],
)
async def create_alert(payload: AlertCreate, db: AsyncSession = Depends(get_db)):
    outbreak = await db.get(Outbreak, payload.outbreak_id)
    if outbreak is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy ổ dịch")
    _require_verified(outbreak)
    farm = await db.get(Farm, payload.farm_id)
    if farm is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy trang trại")
    dup = (
        await db.execute(
            select(Alert.id).where(
                Alert.outbreak_id == payload.outbreak_id, Alert.farm_id == payload.farm_id
            )
        )
    ).scalar_one_or_none()
    if dup:
        raise HTTPException(status.HTTP_409_CONFLICT, "Cảnh báo cho trang trại này đã tồn tại")

    distance_km = 0.0
    loc = geometry_to_location(outbreak.location)
    if loc and farm.location is not None:
        for f, d in await find_farms_within_radius(db, loc["latitude"], loc["longitude"], 20000, False):
            if f.id == farm.id:
                distance_km = d
                break

    alert = Alert(
        outbreak_id=payload.outbreak_id,
        farm_id=payload.farm_id,
        risk_level=payload.risk_level,
        message=payload.message,
        risk_basis="Cảnh báo tạo thủ công bởi cán bộ, mức nguy cơ do người tạo chọn.",
        distance_km=round(distance_km, 3),
    )
    db.add(alert)
    await db.commit()
    await db.refresh(alert)
    return alert


@alert_router.get("/{alert_id}", response_model=AlertResponse)
async def get_alert(
    alert_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current: UserResponse = Depends(get_current_user),
):
    return await _get_visible_or_404(db, alert_id, current)


@alert_router.patch("/{alert_id}/acknowledge", response_model=AlertResponse)
async def acknowledge_alert(
    alert_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current: UserResponse = Depends(get_current_user),
):
    alert = await _get_visible_or_404(db, alert_id, current)
    alert.status = AlertStatus.ACKNOWLEDGED
    await db.commit()
    await db.refresh(alert)
    return alert


@alert_router.put("/{alert_id}", response_model=AlertResponse, dependencies=[Depends(require_staff)])
async def update_alert(alert_id: uuid.UUID, payload: AlertUpdate, db: AsyncSession = Depends(get_db)):
    alert = await _get_or_404(db, alert_id)
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(alert, key, value)
    await db.commit()
    await db.refresh(alert)
    return alert


@alert_router.delete(
    "/{alert_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_staff)]
)
async def delete_alert(alert_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    alert = await _get_or_404(db, alert_id)
    await db.delete(alert)
    await db.commit()


__all__ = ["alert_router"]
