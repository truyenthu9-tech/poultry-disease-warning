"""API truy vấn không gian trên trang trại."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.api.privacy import farm_view
from app.core.database import get_db
from app.schemas.common import Location
from app.schemas.farm import FarmNearby
from app.schemas.user import UserResponse
from app.services.spatial_service import find_farms_within_radius

geo_farms_router = APIRouter()


@geo_farms_router.post("/farms/around", response_model=list[FarmNearby])
async def farms_around(
    location: Location,
    radius_km: float = Query(default=5.0, ge=0.01, le=500.0),
    db: AsyncSession = Depends(get_db),
    current: UserResponse = Depends(get_current_user),
):
    """Tìm trang trại trong bán kính quanh một điểm, sắp xếp gần đến xa."""
    results = await find_farms_within_radius(db, location.latitude, location.longitude, radius_km)
    return [
        FarmNearby(farm=farm_view(f, current), distance_km=round(d, 3)) for f, d in results
    ]


__all__ = ["geo_farms_router"]
