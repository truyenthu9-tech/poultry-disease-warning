"""Kiểm thử các endpoint và schema liên quan đến xác thực người dùng."""

from unittest.mock import MagicMock, patch

import pytest

from app.core.database import get_db
from app.core.security import hash_password, verify_password
from app.schemas.user import UserCreate, UserResponse
from app.schemas.common import BaseResponse


@pytest.fixture
def db_session_mock():
    """Cung cấp phiên làm việc SQLAlchemy (fake) cho các dependency."""
    return MagicMock()


@pytest.fixture
def auth_client(db_session_mock):
    """Khách hàng FastAPI TestClient cho các route xác thực."""
    from fastapi.testclient import TestClient
    from app.api.v1.endpoints import auth as auth_module
    from app.api.v1.api import app

    with patch(
        "app.api.v1.endpoints.auth.get_db",
        return_value=db_session_mock,
    ):
        yield TestClient(app)


def test_verify_password_accepted():
    """Mật khẩu đúng được xác thực thành công."""
    assert verify_password("123456", hash_password("123456")) is True


def test_verify_password_rejected():
    """Mật khẩu sai bị từ chối."""
    assert verify_password("123456", hash_password("654321")) is False


def test_user_create_schema_valid():
    """Schema đăng ký với dữ liệu hợp lệ."""
    payload = UserCreate(
        username="trangtrai_a",
        email="farmer@example.com",
        password="123456",
        role="farmer",
    )
    assert payload.username == "trangtrai_a"
    assert payload.email == "farmer@example.com"
    assert payload.role == "farmer"


def test_user_create_schema_rejects_bad_password():
    """Mật khẩu quá ngắn bị schema từ chối."""
    with pytest.raises(ValueError):
        UserCreate(
            username="trangtrai_a",
            email="farmer@example.com",
            password="12",
            role="farmer",
        )


def test_user_create_schema_rejects_bad_role():
    """Vai trò không hợp lệ bị schema từ chối."""
    with pytest.raises(ValueError):
        UserCreate(
            username="trangtrai_a",
            email="farmer@example.com",
            password="123456",
            role="admin",
        )


def test_user_response_schema():
    """Schema phản hồi sau khi đăng ký thành công."""
    user = UserResponse(
        id="00000000-0000-0000-0000-000000000001",
        username="trangtrai_a",
        email="farmer@example.com",
        role="farmer",
        is_active=True,
    )
    assert user.username == "trangtrai_a"
    assert user.email == "farmer@example.com"


def test_base_response_shape():
    """Phản hồi chuẩn luôn mang status_code và nội dung."""
    resp = BaseResponse(
        status_code=201,
        content={"message": "Đăng ký thành công"},
    )
    assert resp.status_code == 201
    assert resp.content["message"] == "Đăng ký thành công"