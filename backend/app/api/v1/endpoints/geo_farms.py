"""API điểm cuối cho các truy vấn không gian trên trang trại."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.schemas.location import Location
from app.core.database import get_db
from app.models.farm import Farm
from app.services.spatial_service import find_farms_within_radius

router = APIRouter(prefix="/geo", tags=["spatial"])


@router.post("/farms/around", response_model=list[tuple[Farm, float]])
def find_nearby_farms(
    location: Location,
    radius_km: float = Query(default=5.0, ge=0.01, le=500.0, description="Bán kính tìm kiếm bằng km"),
    db: Session = Depends(get_db),
) -> list[tuple[Farm, float]]:
    """
    Tìm tất cả trang trại trong bán kính cho quanh vị trí nhất định.

    - `location`: Điểm trung tâm ở định dạng "longitude latitude" (lon lat).
    - `radius_km`: Bán kính tìm kiếm từ 0.01 đến 500 km.

    Trả về danh sách (farm, distance_km) sắp xếp theo khoảng cách tăng dần.
    """
    if not location.longitude or not location.latitude:
        raise HTTPException(
            status_code=422,
            detail="Cần longitude và latitude hợp lệ.",
        )

    results = find_farms_within_radius(
        db=db,
        location_geometry=f"{location.longitude} {location.latitude}",
        radius_km=radius_km,
    )

    if not results:
        # Không tìm thấy trang trại nào trong bán kính - đây là hành vi bình thường
        return []

    return results


__all__ = ["router"]
