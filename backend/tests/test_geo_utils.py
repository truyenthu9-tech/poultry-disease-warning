"""Tests cho các utility GeoAlchemy2 - không cần Database."""

import math
import pytest
from geoalchemy2 import Geometry
from shapely.geometry import Point

from app.utils.geo import (
    lat_lon_to_wkt,
    wkt_to_lat_lon,
    create_geometry_point,
    validate_point_wkt,
)


@pytest.fixture(autouse=True, scope="function")
def no_db_session(monkeypatch):
    """Đảm bảo không có session DB trong test này."""
    # Không cần fixture DB - chạy thuần Python
    pass


class TestLatLonToWkt:
    """Test chuyển đổi lat/lon -> WKT."""

    def test_valid_hanoi(self):
        """Kiểm tra tọa độ Hà Nội."""
        lat, lon = 21.0285, 105.8542
        wkt = lat_lon_to_wkt(lat, lon)
        assert "SRID=4326;POINT(105.8542 21.0285)" == wkt

    def test_valid_coordinates_range(self):
        """Kiểm tra tọa độ trong phạm vi hợp lệ."""
        # lat range: -90 to 90
        assert lat_lon_to_wkt(0, 0) is not None
        assert "-123.678" in lat_lon_to_wkt(45, -123.678)

    def test_invalid_lat_high(self):
        """Lat vượt quá 90."""
        with pytest.raises(ValueError):
            lat_lon_to_wkt(91.0, 0)

    def test_invalid_lat_low(self):
        """Lat dưới -90."""
        with pytest.raises(ValueError):
            lat_lon_to_wkt(-91.0, 0)

    def test_invalid_lon_high(self):
        """Lon vượt quá 180."""
        with pytest.raises(ValueError):
            lat_lon_to_wkt(0, 181.0)

    def test_invalid_lon_low(self):
        """Lon dưới -180."""
        with pytest.raises(ValueError):
            lat_lon_to_wkt(0, -181.0)


class TestWktToLatLon:
    """Test chuyển đổi WKT -> lat/lon."""

    def test_hanoi_wkt(self):
        """Parse WKT Hà Nội."""
        wkt = "SRID=4326;POINT(105.8542 21.0285)"
        result = wkt_to_lat_lon(wkt)
        assert result is not None
        assert abs(result[0] - 21.0285) < 0.0001
        assert abs(result[1] - 105.8542) < 0.0001

    def test_valid_without_srid(self):
        """WKT không có SRID vẫn parse được."""
        wkt = "POINT(105.8542 21.0285)"
        result = wkt_to_lat_lon(wkt)
        assert result is not None

    def test_invalid_wkt_none(self):
        """WKT không hợp lệ trả về None."""
        assert wkt_to_lat_lon("") is None
        assert wkt_to_lat_lon(None) is None

    def test_invalid_coordinates(self):
        """Tọa độ vượt ngưỡng."""
        result = wkt_to_lat_lon("SRID=4326;POINT(105.85 91.0)")  # lat > 90
        assert result is None


class TestCreateGeometryPoint:
    """Test tạo Geometry cho GeoAlchemy2."""

    def test_hanoi_geometry(self):
        """Tạo geometry điểm Hà Nội."""
        geom = create_geometry_point(105.8542, 21.0285)
        assert isinstance(geom, Geometry)
        # Kiểm tra SRID
        assert geom.srid == 4326

    def test_eu_geometry(self):
        """Tạo geometry ở châu Âu."""
        geom = create_geometry_point(12.4964, 50.1109)  # Warsaw
        assert geom is not None
        assert geom.srid == 4326


class TestValidatePointWkt:
    """Test validate WKT POINT."""

    def test_valid_hanoi_wkt(self):
        """WKT Hà Nội hợp lệ."""
        wkt = "SRID=4326;POINT(105.8542 21.0285)"
        assert validate_point_wkt(wkt) is True

    def test_valid_simple_wkt(self):
        """WKT đơn giản không có SRID."""
        wkt = "POINT(105.85 21.03)"
        assert validate_point_wkt(wkt) is True

    def test_invalid_wkt(self):
        """WKT không hợp lệ."""
        assert validate_point_wkt("") is False
        assert validate_point_wkt("LINESTRING(0 0, 1 1)") is False


class TestRoundTrip:
    """Test round-trip lat/lon -> WKT -> lat/lon."""

    def test_roundtrip_hanoi(self):
        """Chuyển đổi đi và về cho Hà Nội."""
        original_lat = 21.0285
        original_lon = 105.8542
        
        wkt = lat_lon_to_wkt(original_lat, original_lon)
        result = wkt_to_lat_lon(wkt)
        
        assert result is not None
        assert abs(result[0] - original_lat) < 0.0001
        assert abs(result[1] - original_lon) < 0.0001

    def test_roundtrip_warsaw(self):
        """Chuyển đổi đi và về cho Warsaw, Ba Lan."""
        original_lat = 50.1109
        original_lon = 12.4964
        
        wkt = lat_lon_to_wkt(original_lat, original_lon)
        result = wkt_to_lat_lon(wkt)
        
        assert result is not None
        assert abs(result[0] - original_lat) < 0.0001
        assert abs(result[1] - original_lon) < 0.0001


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
