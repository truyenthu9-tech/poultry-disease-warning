"""Dữ liệu mẫu (idempotent). Chạy: python -m app.db.seed_data"""
import asyncio
import secrets
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import async_session_maker, close_db
from app.core.security import hash_password
from app.db.init_db import init_db
from app.models.enums import OutbreakStatus, PoultryType, Severity, UserRole
from app.models.farm import Farm
from app.models.outbreak import Outbreak
from app.models.user import User
from app.utils.geo import location_to_geometry

FARMS = [
    dict(name="Trại gà Đông Anh", owner_name="Nguyễn Văn An", phone="0912345001",
         province="Hà Nội", district="Đông Anh", poultry_type=PoultryType.CHICKEN,
         capacity=5000, lat=21.1370, lon=105.8480),
    dict(name="Trại vịt Sóc Sơn", owner_name="Trần Thị Bình", phone="0912345002",
         province="Hà Nội", district="Sóc Sơn", poultry_type=PoultryType.DUCK,
         capacity=3000, lat=21.2580, lon=105.8480),
    dict(name="Trại gà Gia Lâm", owner_name="Lê Văn Cường", phone="0912345003",
         province="Hà Nội", district="Gia Lâm", poultry_type=PoultryType.CHICKEN,
         capacity=8000, lat=21.0210, lon=105.9430),
    dict(name="Trại ngan Văn Giang", owner_name="Phạm Thị Dung", phone="0912345004",
         province="Hưng Yên", district="Văn Giang", poultry_type=PoultryType.MUSCOVY,
         capacity=2000, lat=20.9340, lon=105.9460),
    dict(name="Trại chim cút Yên Phong", owner_name="Hoàng Văn Em", phone="0912345005",
         province="Bắc Ninh", district="Yên Phong", poultry_type=PoultryType.QUAIL,
         capacity=10000, lat=21.2000, lon=105.9500),
]

OUTBREAKS = [
    dict(virus_type="H5N1", province="Hà Nội", district="Đông Anh",
         status=OutbreakStatus.ACTIVE, severity=Severity.HIGH, cases_count=1200,
         lat=21.1700, lon=105.8480),
    dict(virus_type="H5N6", province="Bắc Ninh", district="Yên Phong",
         status=OutbreakStatus.CONTAINED, severity=Severity.MEDIUM, cases_count=450,
         lat=21.1850, lon=105.9500),
    dict(virus_type="H5N1", province="Hưng Yên", district="Văn Giang",
         status=OutbreakStatus.CLOSED, severity=Severity.LOW, cases_count=80,
         lat=20.9400, lon=105.9500),
]

SAMPLE_USER_EMAIL = "user@poultry-warning.vn"
# Trang trại gán cho tài khoản mẫu, để thử thấy cảnh báo của riêng mình
SAMPLE_OWNED_FARM = "Trại gà Đông Anh"

# Mật khẩu lấy từ SEED_ADMIN_PASSWORD và SEED_USER_PASSWORD, để trống thì sinh ngẫu nhiên
USERS = [
    ("admin@poultry-warning.vn", "Quản trị viên", settings.SEED_ADMIN_PASSWORD, UserRole.ADMIN),
    (SAMPLE_USER_EMAIL, "Người dùng mẫu", settings.SEED_USER_PASSWORD, UserRole.USER),
]


async def seed(db: AsyncSession) -> list[tuple[str, str]]:
    """Nạp dữ liệu mẫu, trả về danh sách tài khoản mới tạo gồm email và mật khẩu."""
    created_users: list[tuple[str, str]] = []
    for email, full_name, password, role in USERS:
        if not (await db.execute(select(User).where(User.email == email))).scalar_one_or_none():
            password = password or secrets.token_urlsafe(12)
            db.add(User(email=email, full_name=full_name, password=hash_password(password), role=role))
            created_users.append((email, password))

    for f in FARMS:
        if not (await db.execute(select(Farm).where(Farm.name == f["name"]))).scalar_one_or_none():
            data = {k: v for k, v in f.items() if k not in ("lat", "lon")}
            db.add(Farm(**data, location=location_to_geometry(f["lat"], f["lon"])))

    for o in OUTBREAKS:
        exists = (
            await db.execute(
                select(Outbreak).where(
                    Outbreak.virus_type == o["virus_type"],
                    Outbreak.province == o["province"],
                    Outbreak.district == o["district"],
                )
            )
        ).scalar_one_or_none()
        if not exists:
            data = {k: v for k, v in o.items() if k not in ("lat", "lon")}
            db.add(
                Outbreak(
                    **data,
                    location=location_to_geometry(o["lat"], o["lon"]),
                    radius_km=settings.DEFAULT_ALERT_RADIUS_KM,
                    reported_date=datetime.now(timezone.utc),
                )
            )
    await db.flush()

    # Gán trang trại mẫu cho tài khoản người dùng mẫu (nếu trang trại chưa có chủ)
    sample_user = (
        await db.execute(select(User).where(User.email == SAMPLE_USER_EMAIL))
    ).scalar_one_or_none()
    owned_farm = (
        await db.execute(select(Farm).where(Farm.name == SAMPLE_OWNED_FARM))
    ).scalar_one_or_none()
    if sample_user is not None and owned_farm is not None and owned_farm.owner_user_id is None:
        owned_farm.owner_user_id = sample_user.id

    await db.commit()
    return created_users


async def main() -> None:
    await init_db()
    async with async_session_maker() as db:
        created_users = await seed(db)
    await close_db()
    print("Seed xong.")
    for email, password in created_users:
        print(f"Tài khoản mới: {email} / {password}")
    if created_users:
        print("Hãy lưu mật khẩu này, nó chỉ được in một lần.")


if __name__ == "__main__":
    asyncio.run(main())
