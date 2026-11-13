"""Utilities cho GeoAlchemy2 và Shapely."""

import uuid
from typing import Optional

from geoalchemy2 import Geometry
from geoalchemy2.shape import from_shape, to_shape
from shapely.geometry import Point


def lat_lon_to_wkt(lat: float, lon: float) -> str:
    """
    Chuyển đổi tọa độ WGS84 (lat, lon) sang định dạng WKT POINT.

    Args:
        lat: Vĩ độ (-90 to 90).
        lon: Kinh độ (-180 to 180).

    Returns:
        String WKT như 'POINT(105.83417 21.02776)' với SRID=4326.
    """
    if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
        raise ValueError("Invalid coordinates: lat must be -90 to 90, lon must be -180 to 180")
    
    point = Point(lon, lat)
    wkt_element = f"SRID=4326;{point.wkt}"
    return wkt_element


def wkt_to_lat_lon(wkt_point: str) -> Optional[tuple[float, float]]:
    """
    Chuyển đổi WKT POINT sang (lat, lon).

    Args:
        wkt_point: String định dạng 'SRID=4326;POINT(lon lat)'.

    Returns:
        Tuple (lat, lon) hoặc None nếu không hợp lệ.
    """
    try:
        # WKT format: SRID=4326;POINT(lon lat)
        if wkt_point.startswith("SRID="):
            point_str = wkt_point.split(";")[1]
        else:
            return None
        
        point = Point(*[float(x) for x in point_str.strip().split()[-2:]])
        lon, lat = point.x, point.y
        # Ensure valid range
        if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
            return None
        
        return (lat, lon)
    except Exception:
        return None


def create_geometry_point(lon: float, lat: float) -> Geometry:
    """
    Tạo đối tượng Geometry cho GeoAlchemy2 với SRID=4326.

    Args:
        lon: Kinh độ WGS84.
        lat: Vĩ độ WGS84.

    Returns:
        geometry_column(POINT(lat,lon), srid=4326) như 'SRID=4326;POINT(lon lat)'.
    """
    return from_shape(Point(lon, lat)).geom  # GeoAlchemy2 stores lon,lat order


def validate_point_wkt(wkt_str: str) -> bool:
    """Kiểm tra string có phải POINT hợp lệ với SRID=4326."""
    if wkt_str.startswith("SRID="):
        point = Point(*[float(x) for x in wkt_str.split(";")[1].split()[-2:]])
        return True
    return False


__all__ = [
    "lat_lon_to_wkt",
    "wkt_to_lat_lon",
    "create_geometry_point",
    "validate_point_wkt",
]
