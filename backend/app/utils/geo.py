"""Chuyển đổi tọa độ (lat, lon) <-> Geometry. Đây là nơi duy nhất làm việc này."""
from geoalchemy2.elements import WKBElement
from geoalchemy2.shape import from_shape, to_shape
from shapely.geometry import Point


def location_to_geometry(lat: float, lon: float) -> WKBElement:
    """Thứ tự bắt buộc của Point là (longitude, latitude)."""
    if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
        raise ValueError("Tọa độ không hợp lệ")
    return from_shape(Point(lon, lat), srid=4326)


def geometry_to_location(geom) -> dict | None:
    if geom is None:
        return None
    point = to_shape(geom)
    return {"latitude": point.y, "longitude": point.x}


__all__ = ["location_to_geometry", "geometry_to_location"]
