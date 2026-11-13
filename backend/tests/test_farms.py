"""Test API quản lý trang trại."""
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.farm import Farm, FarmStatus, FarmType
from app.utils.geo import GeoPoint

from .conftest import farm, get_token


def test_create_and_get_farm(client: TestClient, farm: dict, auth_headers: dict):
    """Kiểm tra tạo và lấy farm."""
    response = client.post(
        "/api/v1/farms",
        json={**farm, "owner_name": "Nguyễn Văn A", "address": "Thôn Trại Mới"},
        headers=auth_headers,
    )
    assert response.status_code == 201
    data = response.json()["data"]
    assert data["owner_name"] == "Nguyễn Văn A"
    assert data["province"] == "Hà Nội"

    get_response = client.get(
        f"/api/v1/farms/{data['id']}", headers=auth_headers
    )
    assert get_response.status_code == 200


def test_list_farms(client: TestClient):
    """Kiểm tra danh sách farm."""
    response = client.get("/api/v1/farms", headers={"Authorization": "Bearer x"})
    assert response.status_code == 200
    assert isinstance(response.json()["data"], list)


def test_update_farm(client: TestClient, farm: dict, auth_headers: dict):
    """Kiểm tra cập nhật farm."""
    response = client.post(
        "/api/v1/farms",
        json={**farm, "owner_name": "Nguyễn Văn A", "address": "Thôn Trại Mới"},
        headers=auth_headers,
    )
    farm_id = response.json()["data"]["id"]

    update_response = client.put(
        f"/api/v1/farms/{farm_id}",
        json={
            "owner_name": "Trần Thị B",
            "province": "Hà Nội",
            "farm_type": "layer",
        },
        headers=auth_headers,
    )
    assert update_response.status_code == 200
    assert update_response.json()["data"]["owner_name"] == "Trần Thị B"
    assert update_response.json()["data"]["farm_type"] == "layer"


def test_delete_farm(client: TestClient, farm: dict, auth_headers: dict):
    """Kiểm tra xóa farm."""
    response = client.post(
        "/api/v1/farms",
        json={**farm, "owner_name": "Nguyễn Văn A", "address": "Thôn Trại Mới"},
        headers=auth_headers,
    )
    farm_id = response.json()["data"]["id"]

    delete_response = client.delete(
        f"/api/v1/farms/{farm_id}", headers=auth_headers
    )
    assert delete_response.status_code == 204


def test_invalid_coordinates(client: TestClient, auth_headers: dict):
    """Kiểm tra toạ độ không hợp lệ."""
    response = client.post(
        "/api/v1/farms",
        json={
            "owner_name": "Nguyễn Văn A",
            "address": "Thôn Trại Mới",
            "province": "Hà Nội",
            "latitude": 999.0,
            "longitude": 105.65,
        },
        headers=auth_headers,
    )
    assert response.status_code == 422


def test_farm_model(db_session: Session):
    """Kiểm tra model farm."""
    db_session.add(
        Farm(
            owner_name="Nguyễn Văn A",
            address="Thôn Trại Mới",
            province="Hà Nội",
            district="Phú Xuyên",
            latitude=20.35,
            longitude=105.65,
            farm_type=FarmType.BROILER,
            status=FarmStatus.ACTIVE,
        )
    )
    db_session.commit()
    farm = db_session.get(Farm, None)
    assert farm is not None
    assert farm.latitude == 20.35
    assert farm.longitude == 105.65