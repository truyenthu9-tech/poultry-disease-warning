"""Test API quản lý dịch bệnh."""
from fastapi.testclient import TestClient

from app.models.outbreak import Disease, OutbreakStatus
from app.utils.geo import GeoPoint

from .conftest import farm, get_token


def test_create_outbreak(client: TestClient, farm: dict, auth_headers: dict):
    """Kiểm tra tạo dịch bệnh."""
    response = client.post(
        "/api/v1/outbreaks",
        json={
            "farm_id": farm["id"],
            "disease": "newcastle",
            "symptom": "Tràn dịch ở hốc mắt, chảy máu mũi",
            "description": "Dịch Newcastle.",
        },
        headers=auth_headers,
    )
    assert response.status_code == 201
    data = response.json()["data"]
    assert data["disease"] == "newcastle"


def test_list_outbreaks(client: TestClient):
    """Kiểm tra danh sách dịch bệnh."""
    response = client.get("/api/v1/outbreaks", headers={"Authorization": "Bearer x"})
    assert response.status_code == 200
    assert isinstance(response.json()["data"], list)


def test_get_outbreak(client: TestClient, farm: dict, auth_headers: dict):
    """Kiểm tra lấy dịch bệnh."""
    response = client.post(
        "/api/v1/outbreaks",
        json={
            "farm_id": farm["id"],
            "disease": "newcastle",
            "symptom": "Tràn dịch ở hốc mắt",
        },
        headers=auth_headers,
    )
    outbreak_id = response.json()["data"]["id"]

    get_response = client.get(
        f"/api/v1/outbreaks/{outbreak_id}", headers=auth_headers
    )
    assert get_response.status_code == 200
    assert get_response.json()["data"]["disease"] == "newcastle"


def test_update_outbreak(client: TestClient, farm: dict, auth_headers: dict):
    """Kiểm tra cập nhật dịch bệnh."""
    response = client.post(
        "/api/v1/outbreaks",
        json={
            "farm_id": farm["id"],
            "disease": "newcastle",
            "symptom": "Tràn dịch ở hốc mắt",
        },
        headers=auth_headers,
    )
    outbreak_id = response.json()["data"]["id"]

    update_response = client.put(
        f"/api/v1/outbreaks/{outbreak_id}",
        json={
            "disease": "gumboro",
            "status": "confirmed",
            "description": "Cập nhật mô tả.",
        },
        headers=auth_headers,
    )
    assert update_response.status_code == 200
    assert update_response.json()["data"]["disease"] == "gumboro"
    assert update_response.json()["data"]["status"] == "confirmed"


def test_delete_outbreak(client: TestClient, farm: dict, auth_headers: dict):
    """Kiểm tra xóa dịch bệnh."""
    response = client.post(
        "/api/v1/outbreaks",
        json={
            "farm_id": farm["id"],
            "disease": "newcastle",
            "symptom": "Tràn dịch ở hốc mắt",
        },
        headers=auth_headers,
    )
    outbreak_id = response.json()["data"]["id"]

    delete_response = client.delete(
        f"/api/v1/outbreaks/{outbreak_id}", headers=auth_headers
    )
    assert delete_response.status_code == 204


def test_outbreak_model(db_session):
    """Kiểm tra model outbreak."""
    from app.models.outbreak import Outbreak

    db_session.add(
        Outbreak(
            disease=Disease.NEWTONS,
            symptom="Tràn dịch ở hốc mắt",
            status=OutbreakStatus.CONFIRMED,
            farm_id=farm["id"],
        )
    )
    db_session.commit()
    outbreak = db_session.query(Outbreak).first()
    assert outbreak is not None
    assert outbreak.disease == Disease.NEWTONS