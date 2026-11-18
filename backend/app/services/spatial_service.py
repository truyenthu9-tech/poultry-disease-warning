"""Truy vấn không gian bằng PostGIS trên kiểu geography (đơn vị mét)."""
from sqlalchemy import cast, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from geoalchemy2 import Geography

from app.models.farm import Farm


async def find_farms_within_radius(
    db: AsyncSession,
    lat: float,
    lon: float,
    radius_km: float,
    only_active: bool = True,
) -> list[tuple[Farm, float]]:
    """Trả về [(farm, distance_km)] sắp xếp gần đến xa."""
    point = cast(func.ST_SetSRID(func.ST_MakePoint(lon, lat), 4326), Geography)
    farm_geog = cast(Farm.location, Geography)
    distance_m = func.ST_Distance(farm_geog, point)

    stmt = (
        select(Farm, distance_m.label("distance_m"))
        .where(Farm.location.is_not(None))
        .where(func.ST_DWithin(farm_geog, point, radius_km * 1000.0))
        .order_by(distance_m)
    )
    if only_active:
        stmt = stmt.where(Farm.is_active.is_(True))

    rows = (await db.execute(stmt)).all()
    return [(farm, float(dist) / 1000.0) for farm, dist in rows]


__all__ = ["find_farms_within_radius"]
