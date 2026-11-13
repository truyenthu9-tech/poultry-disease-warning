"""Dịch vụ xử lý toạ độ và khoảng cách giữa các điểm bằng PostGIS."""

from typing import Optional, Tuple

from sqlalchemy import func, text, cast as sa_cast
from sqlalchemy.orm import Session

from app.models.farm import Farm


def find_farms_within_radius(
    db: Session,
    location_geometry: str,
    radius_km: float = 5.0,
) -> list[Tuple[Optional[Farm], Optional[float]]]:
    """
    Tìm tất cả trang trại trong bán kính cho trước từ vị trí ổ dịch.

    Args:
        db: Database session (AsyncSession hoặc Sync Session được inject rõ ràng)
        location_geometry: WKT hình học điểm ở định dạng 'SRID=4326;POINT(lon lat)'
        radius_km: Bán kính tìm kiếm bằng km

    Returns:
        Danh sách tuple (farm_instance, distance_km) sắp xếp theo khoảng cách tăng dần.
        Farm có null location sẽ bị bỏ qua.

    Notes:
        - Farm.location là Geography column (GeoAlchemy2 Geometry với srid=4326)
        - Cast `geom::geography` để sử dụng ST_DWithin và ST_Distance
        - WKT yêu cầu thứ tự "longitude latitude" (lon lat) với SRID=4326
        - Khoảng cách tính bằng mét trên geography, chuyển sang km ở cuối

    PostGIS reference:
        https://postgis.net/docs/ST_DWithin.html
        https://postgis.net/docs/ST_GeographyFromText.html

    Blocker (for review):
        - Nếu Farm.location định nghĩa là Geometry thay vì Geography thì cần explicit cast
        - AsyncSession injection cần đảm bảo để tránh connection leaks
    """

    # Chuyển đổi bán kính từ km sang mét cho PostGIS (SRID 4326)
    radius_m = radius_km * 1000.0

    # Tạo query point từ WKT string với ST_GeographyFromText
    # Format: 'SRID=4326;POINT(lon lat)' - lon trước, lat sau
    query_point_geom = func.ST_GeographyFromText(f"SRID=4326;{location_geometry}")

    # Query tìm farm trong bán kính sử dụng ST_DWithin trên geography column
    # Farm.location được định nghĩa với Geometry(geometry_type="POINT", srid=4326)
    # Cast thành geography cho spatial functions
    condition = func.ST_DWithin(sa_cast(Farm.location, "geography"), query_point_geom, radius_m)

    # Query trả về farm và khoảng cách tính bằng ST_Distance (true = use geodetic)
    from sqlalchemy import func
    
    distance_expr = sa_cast(func.ST_Distance(sa_cast(Farm.location, "geography"), query_point_geom), "float") / 1000.0

    # Query: get all matching farms ordered by distance
    result = db.query(Farm, distance_expr).filter(
        Farm.location.isnot(None),
        condition == True
    ).order_by(distance_expr).limit(None)

    return result.all()


__all__ = ["find_farms_within_radius"]
