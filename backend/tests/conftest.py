"""Fixture và cấu hình chung cho các test."""
from collections.abc import Callable
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.database import get_db


@pytest.fixture
def client() -> TestClient:
    """Khởi tạo client test."""
    from app.main import app

    with TestClient(app) as c:
        yield c


@pytest.fixture
def db_session() -> Session:
    """Phiên làm việc với cơ sở dữ liệu."""
    from app.db.init_db import SessionLocal

    with SessionLocal() as s:
        yield s


@pytest.fixture
def init_database() -> Callable[[Session], None]:
    """Khởi tạo lại cơ sở dữ liệu trước mỗi test."""

    def _init(db: Session) -> None:
        from app.db.init_db import init_db

        init_db()

    return _init


@pytest.fixture
def admin_client() -> Any:
    """Client đăng nhập với tài khoản admin."""
    from app.api.v1.endpoints.auth import oauth2_scheme

    response = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@poultry-warning.local", "password": "admin123"},
    )
    assert response.status_code == 200
    return response.json()


@pytest.fixture
def user_client() -> Any:
    """Client đăng nhập với tài khoản người dùng."""
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "user@poultry-warning.local", "password": "user123"},
    )
    assert response.status_code == 200
    return response.json()


@pytest.fixture
def auth_headers(admin_client: dict[str, Any]) -> dict[str, str]:
    """Header token của admin."""
    return {"Authorization": f"Bearer {admin_client['access_token']}"}


@pytest.fixture
def user_headers(user_client: dict[str, Any]) -> dict[str, str]:
    """Header token của người dùng."""
    return {"Authorization": f"Bearer {user_client['access_token']}"}


@pytest.fixture
def farm() -> dict[str, Any]:
    """Dữ liệu farm mẫu."""
    return {
        "owner_name": "Nguyễn Văn A",
        "address": "Thôn Trại Mới, Xã Tân Hòa, Huyện Phú Xuyên",
        "province": "Hà Nội",
        "district": "Phú Xuyên",
        "latitude": 20.35,
        "longitude": 105.65,
        "farm_type": "broiler",
        "phone": "0912345678",
    }


@pytest.fixture
def outbreak() -> dict[str, Any]:
    """Dữ liệu outbreak mẫu."""
    return {
        "farm_id": None,  # sẽ thay bằng farm_id thực tế
        "disease": "newcastle",
        "symptom": "Tràn dịch ở hốc mắt, chảy máu mũi",
        "description": "Dịch Newcastle.",
    }


def get_token(username: str, password: str) -> str:
    """Trả về token truy cập."""
    response = client.post(
        "/api/v1/auth/login",
        json={"email": username, "password": password},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


__all__ = ["client", "db_session", "init_database", "admin_client", "user_client", "auth_headers", "user_headers", "farm", "outbreak", "get_token"]