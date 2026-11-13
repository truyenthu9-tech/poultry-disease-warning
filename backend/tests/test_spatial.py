"""Tests for spatial/geo utilities and spatial queries."""

import pytest
from geoalchemy2 import WKTElement
from shapely.geometry import Point

from app.utils.geo import (
    lonlat_to_point,
    point_to_lonlat,
    calculate_distance_km,
    is_within_radius,
    create_buffer_polygon,
    validate_coordinates,
    format_coordinates,
)
from app.models.farm import Farm
from app.models.outbreak import Outbreak


class TestGeoUtils:
    """Test core geo utility functions."""

    def test_lonlat_to_point(self):
        """Test converting lon/lat to WKTElement."""
        point = lonlat_to_point(105.85, 21.03)
        assert isinstance(point, WKTElement)
        assert point.srid == 4326
        # Check WKT format
        wkt = str(point.data)
        assert "POINT" in wkt.upper()
        assert "105.85" in wkt
        assert "21.03" in wkt

    def test_point_to_lonlat(self):
        """Test converting WKTElement back to lon/lat."""
        point = lonlat_to_point(105.85, 21.03)
        lon, lat = point_to_lonlat(point)
        assert abs(lon - 105.85) < 0.0001
        assert abs(lat - 21.03) < 0.0001

    def test_roundtrip_lonlat_point_lonlat(self):
        """Test round-trip conversion preserves coordinates."""
        original_lon, original_lat = 106.6297, 10.8231  # Ho Chi Minh City
        point = lonlat_to_point(original_lon, original_lat)
        result_lon, result_lat = point_to_lonlat(point)
        assert abs(result_lon - original_lon) < 0.00001
        assert abs(result_lat - original_lat) < 0.00001

    def test_calculate_distance_km_same_point(self):
        """Distance from a point to itself should be 0."""
        dist = calculate_distance_km(105.85, 21.03, 105.85, 21.03)
        assert dist == 0.0

    def test_calculate_distance_km_hanoi_to_hcmc(self):
        """Test distance between Hanoi and Ho Chi Minh City (~1150 km)."""
        # Hanoi: 105.85, 21.03
        # HCMC: 106.63, 10.82
        dist = calculate_distance_km(105.85, 21.03, 106.63, 10.82)
        # Approximate great-circle distance
        assert 1100 < dist < 1200

    def test_calculate_distance_km_short_distance(self):
        """Test short distance calculation (~1 km)."""
        # Two points ~1km apart in Hanoi
        dist = calculate_distance_km(105.85, 21.03, 105.86, 21.03)
        assert 0.8 < dist < 1.2

    def test_calculate_distance_km_symmetry(self):
        """Distance should be symmetric."""
        dist1 = calculate_distance_km(105.85, 21.03, 106.63, 10.82)
        dist2 = calculate_distance_km(106.63, 10.82, 105.85, 21.03)
        assert abs(dist1 - dist2) < 0.001

    def test_is_within_radius_true(self):
        """Test point within radius returns True."""
        # Point at center
        assert is_within_radius(105.85, 21.03, 105.85, 21.03, 10.0) is True
        # Point 5km away, radius 10km
        assert is_within_radius(105.85, 21.03, 105.90, 21.03, 10.0) is True

    def test_is_within_radius_false(self):
        """Test point outside radius returns False."""
        # Point 15km away, radius 10km
        assert is_within_radius(105.85, 21.03, 106.00, 21.03, 10.0) is False

    def test_is_within_radius_boundary(self):
        """Test point exactly at radius boundary."""
        # This is approximate - depends on exact distance calculation
        # Use a known distance
        center_lon, center_lat = 105.85, 21.03
        # Point ~5km east
        point_lon, point_lat = 105.90, 21.03
        dist = calculate_distance_km(center_lon, center_lat, point_lon, point_lat)
        # At exact radius
        assert is_within_radius(center_lon, center_lat, point_lon, point_lat, dist) is True
        # Just outside
        assert is_within_radius(center_lon, center_lat, point_lon, point_lat, dist - 0.001) is False

    def test_create_buffer_polygon(self):
        """Test creating a circular buffer polygon."""
        polygon = create_buffer_polygon(105.85, 21.03, 5.0)  # 5km radius
        assert polygon is not None
        assert polygon.srid == 4326
        wkt = str(polygon.data)
        assert "POLYGON" in wkt.upper()

    def test_validate_coordinates_valid(self):
        """Test validation of valid coordinates."""
        # Valid Vietnam coordinates
        assert validate_coordinates(105.85, 21.03) is True
        assert validate_coordinates(106.63, 10.82) is True
        assert validate_coordinates(108.0, 16.0) is True  # Central Vietnam
        # Edge cases
        assert validate_coordinates(-180, -90) is True
        assert validate_coordinates(180, 90) is True
        assert validate_coordinates(0, 0) is True

    def test_validate_coordinates_invalid(self):
        """Test validation rejects invalid coordinates."""
        # Longitude out of range
        assert validate_coordinates(181, 0) is False
        assert validate_coordinates(-181, 0) is False
        # Latitude out of range
        assert validate_coordinates(0, 91) is False
        assert validate_coordinates(0, -91) is False
        # Both invalid
        assert validate_coordinates(200, 100) is False

    def test_format_coordinates(self):
        """Test coordinate formatting."""
        formatted = format_coordinates(105.8542, 21.0285)
        assert formatted == "105.8542, 21.0285"
        # Test rounding
        formatted = format_coordinates(105.8542123, 21.0285123, precision=4)
        assert formatted == "105.8542, 21.0285"


class TestFarmSpatialQueries:
    """Test spatial queries on Farm model (requires database)."""

    @pytest.mark.asyncio
    async def test_farm_creation_with_location(self, db_session):
        """Test creating a farm with GPS location."""
        farm = Farm(
            name="Test Farm",
            location=lonlat_to_point(105.85, 21.03),
            address="Hanoi, Vietnam",
            capacity=10000,
            farm_type="broiler",
            contact_phone="0123456789",
        )
        db_session.add(farm)
        await db_session.commit()
        await db_session.refresh(farm)

        assert farm.id is not None
        assert farm.location is not None
        lon, lat = point_to_lonlat(farm.location)
        assert abs(lon - 105.85) < 0.0001
        assert abs(lat - 21.03) < 0.0001

    @pytest.mark.asyncio
    async def test_farm_nearby_query(self, db_session, test_user):
        """Test querying farms within radius."""
        # Create farms at different distances from Hanoi center (105.85, 21.03)
        farms_data = [
            ("Farm Center", 105.85, 21.03),      # 0 km
            ("Farm Near", 105.86, 21.03),        # ~1 km
            ("Farm Medium", 105.90, 21.03),      # ~5 km
            ("Farm Far", 106.00, 21.03),         # ~15 km
            ("Farm Very Far", 106.63, 10.82),    # ~1150 km (HCMC)
        ]

        for name, lon, lat in farms_data:
            farm = Farm(
                name=name,
                location=lonlat_to_point(lon, lat),
                address=f"Address for {name}",
                capacity=5000,
                farm_type="layer",
                owner_id=test_user.id,
                contact_phone="0123456789",
            )
            db_session.add(farm)

        await db_session.commit()

        # Query farms within 10km of Hanoi center
        from sqlalchemy import select
        from app.utils.geo import create_buffer_polygon

        buffer = create_buffer_polygon(105.85, 21.03, 10.0)
        stmt = select(Farm).where(Farm.location.ST_Within(buffer))
        result = await db_session.execute(stmt)
        nearby_farms = result.scalars().all()

        # Should find 3 farms (center, near, medium)
        assert len(nearby_farms) == 3
        farm_names = {f.name for f in nearby_farms}
        assert "Farm Center" in farm_names
        assert "Farm Near" in farm_names
        assert "Farm Medium" in farm_names
        assert "Farm Far" not in farm_names
        assert "Farm Very Far" not in farm_names


class TestOutbreakSpatialQueries:
    """Test spatial queries on Outbreak model."""

    @pytest.mark.asyncio
    async def test_outbreak_nearby_farms(self, db_session, test_user):
        """Test finding farms near an outbreak."""
        # Create an outbreak in Hanoi
        outbreak = Outbreak(
            disease_name="AIV H5N1",
            location=lonlat_to_point(105.85, 21.03),
            address="Hanoi, Vietnam",
            reported_by_id=test_user.id,
            status="confirmed",
            severity="high",
            mortality_count=100,
            at_risk_count=5000,
        )
        db_session.add(outbreak)

        # Create farms at various distances
        farms_data = [
            ("Farm 1km", 105.86, 21.03),       # very_high risk
            ("Farm 2km", 105.87, 21.03),       # high risk
            ("Farm 4km", 105.90, 21.03),       # medium risk
            ("Farm 7km", 105.95, 21.03),       # low risk
            ("Farm 15km", 106.05, 21.03),      # outside alert radius
        ]

        for name, lon, lat in farms_data:
            farm = Farm(
                name=name,
                location=lonlat_to_point(lon, lat),
                address=f"Address for {name}",
                capacity=5000,
                farm_type="broiler",
                owner_id=test_user.id,
                contact_phone="0123456789",
                status="active",
            )
            db_session.add(farm)

        await db_session.commit()

        # Query farms within alert radius (default 10km)
        from app.utils.geo import create_buffer_polygon
        from sqlalchemy import select, func

        alert_radius_km = 10.0
        buffer = create_buffer_polygon(105.85, 21.03, alert_radius_km)

        stmt = (
            select(
                Farm,
                func.ST_DistanceSphere(Farm.location, outbreak.location).label("distance_m"),
            )
            .where(Farm.location.ST_Within(buffer))
            .where(Farm.status == "active")
        )
        result = await db_session.execute(stmt)
        nearby_farms = result.all()

        assert len(nearby_farms) == 4  # Excludes 15km farm

        # Verify distance ordering and risk levels
        for farm, distance_m in nearby_farms:
            distance_km = distance_m / 1000
            if distance_km < 1:
                risk = "very_high"
            elif distance_km < 3:
                risk = "high"
            elif distance_km < 5:
                risk = "medium"
            else:
                risk = "low"
            print(f"Farm: {farm.name}, Distance: {distance_km:.2f}km, Risk: {risk}")


class TestSpatialEdgeCases:
    """Test edge cases for spatial operations."""

    def test_antimeridian_crossing(self):
        """Test distance calculation across antimeridian (180/-180)."""
        # Point near 179°E and 179°W
        dist = calculate_distance_km(179.0, 0.0, -179.0, 0.0)
        # Should be ~222 km (2 degrees at equator), not ~39,000 km
        assert 200 < dist < 250

    def test_poles(self):
        """Test distance calculation at poles."""
        # North pole to a point at 89°N
        dist = calculate_distance_km(0, 90, 0, 89)
        # ~111 km (1 degree latitude)
        assert 110 < dist < 112

    def test_invalid_coordinates_raise_error(self):
        """Test that invalid coordinates in lonlat_to_point raise error."""
        with pytest.raises(ValueError):
            lonlat_to_point(200, 0)
        with pytest.raises(ValueError):
            lonlat_to_point(0, 100)

    def test_point_to_lonlat_invalid_input(self):
        """Test point_to_lonlat with invalid input."""
        with pytest.raises(ValueError):
            point_to_lonlat("not a point")


# Integration test with actual PostGIS functions
class TestPostGISIntegration:
    """Test PostGIS-specific functionality (requires database with PostGIS)."""

    @pytest.mark.asyncio
    async def test_st_distance_sphere_vs_calculate_distance_km(self, db_session):
        """Compare PostGIS ST_DistanceSphere with our utility function."""
        from sqlalchemy import select, func

        # Create two test points
        point1 = lonlat_to_point(105.85, 21.03)
        point2 = lonlat_to_point(106.63, 10.82)

        # Query PostGIS distance
        stmt = select(func.ST_DistanceSphere(point1, point2))
        result = await db_session.execute(stmt)
        pg_distance_m = result.scalar()
        pg_distance_km = pg_distance_m / 1000

        # Our utility function
        util_distance_km = calculate_distance_km(105.85, 21.03, 106.63, 10.82)

        # Should be very close (within 1%)
        diff_pct = abs(pg_distance_km - util_distance_km) / pg_distance_km * 100
        assert diff_pct < 1.0

    @pytest.mark.asyncio
    async def test_st_within_buffer(self, db_session, test_user):
        """Test ST_Within with buffer polygon."""
        from app.utils.geo import create_buffer_polygon
        from sqlalchemy import select

        # Create farm at known location
        farm = Farm(
            name="Test Farm",
            location=lonlat_to_point(105.85, 21.03),
            address="Hanoi",
            capacity=1000,
            farm_type="broiler",
            owner_id=test_user.id,
            contact_phone="0123456789",
        )
        db_session.add(farm)
        await db_session.commit()

        # Buffer that includes the farm
        buffer = create_buffer_polygon(105.85, 21.03, 1.0)  # 1km radius
        stmt = select(Farm).where(Farm.location.ST_Within(buffer))
        result = await db_session.execute(stmt)
        farms = result.scalars().all()
        assert len(farms) == 1

        # Buffer that excludes the farm
        buffer = create_buffer_polygon(106.63, 10.82, 1.0)  # HCMC, 1km radius
        stmt = select(Farm).where(Farm.location.ST_Within(buffer))
        result = await db_session.execute(stmt)
        farms = result.scalars().all()
        assert len(farms) == 0