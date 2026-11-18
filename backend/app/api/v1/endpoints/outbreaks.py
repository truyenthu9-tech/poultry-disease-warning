"""API quản lý ổ dịch."""
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_staff
from app.api.privacy import farm_view
from app.core.config import settings
from app.core.database import get_db
from app.models.enums import OutbreakStatus
from app.models.outbreak import Outbreak
from app.schemas.farm import FarmNearby
from app.schemas.outbreak import OutbreakCreate, OutbreakImportResult, OutbreakResponse, OutbreakUpdate
from app.schemas.user import UserResponse
from app.services.crawler_service import run_import
from app.services.spatial_service import find_farms_within_radius
from app.utils.geo import geometry_to_location, location_to_geometry

outbreak_router = APIRouter(prefix="/outbreaks")


async def _get_or_404(db: AsyncSession, outbreak_id: uuid.UUID) -> Outbreak:
    outbreak = await db.get(Outbreak, outbreak_id)
    if outbreak is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy ổ dịch")
    return outbreak


@outbreak_router.post(
    "", response_model=OutbreakResponse, status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_staff)],
)
async def create_outbreak(
    payload: OutbreakCreate,
    db: AsyncSession = Depends(get_db),
    current: UserResponse = Depends(require_staff),
):
    data = payload.model_dump(exclude={"location", "radius_km", "reported_date"})
    outbreak = Outbreak(
        **data,
        location=location_to_geometry(payload.location.latitude, payload.location.longitude),
        radius_km=payload.radius_km or settings.DEFAULT_ALERT_RADIUS_KM,
        # Cán bộ nhập tay: coi là đã xác nhận, ghi lại người nhập
        source="manual",
        verified=True,
        verified_at=datetime.now(timezone.utc),
        verified_by_id=current.id,
    )
    if payload.reported_date:
        outbreak.reported_date = payload.reported_date
    db.add(outbreak)
    await db.commit()
    await db.refresh(outbreak)
    return outbreak


@outbreak_router.post(
    "/import", response_model=OutbreakImportResult, dependencies=[Depends(require_staff)]
)
async def import_outbreaks(db: AsyncSession = Depends(get_db)):
    """Nhập ổ dịch từ các nguồn dữ liệu đã cấu hình (OUTBREAK_FEED_URLS).

    Bản ghi mới ở trạng thái chưa xác nhận và không tự tạo cảnh báo. Chưa cấu hình nguồn nào
    thì không nhập gì và sources_configured bằng 0.
    """
    return await run_import(db)


@outbreak_router.post("/{outbreak_id}/verify", response_model=OutbreakResponse)
async def verify_outbreak(
    outbreak_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current: UserResponse = Depends(require_staff),
):
    """Cán bộ xác nhận ổ dịch là thật và thông tin đúng. Sau đó mới tạo được cảnh báo."""
    outbreak = await _get_or_404(db, outbreak_id)
    if not outbreak.verified:
        outbreak.verified = True
        outbreak.verified_at = datetime.now(timezone.utc)
        outbreak.verified_by_id = current.id
        await db.commit()
        await db.refresh(outbreak)
    return outbreak


@outbreak_router.get("", response_model=list[OutbreakResponse])
async def list_outbreaks(
    status_: OutbreakStatus | None = Query(default=None, alias="status"),
    virus_type: str | None = None,
    province: str | None = None,
    verified: bool | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Outbreak)
    if verified is not None:
        stmt = stmt.where(Outbreak.verified.is_(verified))
    if status_:
        stmt = stmt.where(Outbreak.status == status_)
    if virus_type:
        stmt = stmt.where(Outbreak.virus_type == virus_type)
    if province:
        stmt = stmt.where(Outbreak.province == province)
    stmt = stmt.order_by(Outbreak.reported_date.desc()).offset((page - 1) * page_size).limit(page_size)
    return list((await db.execute(stmt)).scalars())


@outbreak_router.get("/{outbreak_id}", response_model=OutbreakResponse)
async def get_outbreak(outbreak_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    return await _get_or_404(db, outbreak_id)


@outbreak_router.get("/{outbreak_id}/nearby-farms", response_model=list[FarmNearby])
async def nearby_farms(
    outbreak_id: uuid.UUID,
    radius_km: float = Query(default=settings.DEFAULT_ALERT_RADIUS_KM, gt=0, le=500),
    db: AsyncSession = Depends(get_db),
    current: UserResponse = Depends(get_current_user),
):
    outbreak = await _get_or_404(db, outbreak_id)
    loc = geometry_to_location(outbreak.location)
    if loc is None:
        return []
    results = await find_farms_within_radius(db, loc["latitude"], loc["longitude"], radius_km)
    return [
        FarmNearby(farm=farm_view(farm, current), distance_km=round(dist, 3))
        for farm, dist in results
    ]


@outbreak_router.put(
    "/{outbreak_id}", response_model=OutbreakResponse, dependencies=[Depends(require_staff)]
)
async def update_outbreak(
    outbreak_id: uuid.UUID, payload: OutbreakUpdate, db: AsyncSession = Depends(get_db)
):
    outbreak = await _get_or_404(db, outbreak_id)
    data = payload.model_dump(exclude_unset=True, exclude={"location"})
    for key, value in data.items():
        setattr(outbreak, key, value)
    if payload.location is not None:
        outbreak.location = location_to_geometry(payload.location.latitude, payload.location.longitude)
    await db.commit()
    await db.refresh(outbreak)
    return outbreak


@outbreak_router.delete(
    "/{outbreak_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_staff)]
)
async def delete_outbreak(outbreak_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    outbreak = await _get_or_404(db, outbreak_id)
    await db.delete(outbreak)
    await db.commit()


__all__ = ["outbreak_router"]
