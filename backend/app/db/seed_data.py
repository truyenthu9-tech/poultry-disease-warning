"""Dữ liệu mẫu khởi tạo cho hệ thống."""
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.alert import Alert, AlertSeverity, AlertStatus
from app.models.farm import Farm, FarmStatus, FarmType
from app.models.outbreak import Disease, Outbreak, OutbreakStatus
from app.models.user import User, UserRole

from app.core.database import get_db


def seed(db: Session) -> None:
    """Tạo dữ liệu mẫu nếu chưa có."""

    # --- Người dùng ---
    if db.query(User).count() == 0:
        admin = User(
            email="admin@poultry-warning.local",
            full_name="Quản trị viên",
            password="admin123",
            role=UserRole.ADMIN,
            is_active=True,
        )
        db.add(admin)

        user = User(
            email="user@poultry-warning.local",
            full_name="Người dùng mẫu",
            password="user123",
            role=UserRole.USER,
            is_active=True,
        )
        db.add(user)

    # --- Trang trại ---
    if db.query(Farm).count() == 0:
        farms = [
            Farm(
                owner_name="Nguyễn Văn A",
                address="Thôn Trại Mới, Xã Tân Hòa, Huyện Phú Xuyên",
                province="Hà Nội",
                district="Phú Xuyên",
                latitude=20.35,
                longitude=105.65,
                farm_type=FarmType.BROILER,
                status=FarmStatus.ACTIVE,
                phone="0912345678",
            ),
            Farm(
                owner_name="Trần Thị B",
                address="Thôn Làng Chài, Xã Minh Châu, Huyện Thường Tín",
                province="Hà Nội",
                district="Thường Tín",
                latitude=20.25,
                longitude=105.75,
                farm_type=FarmType.LAYER,
                status=FarmStatus.ACTIVE,
                phone="0912345679",
            ),
            Farm(
                owner_name="Lê Văn C",
                address="Thôn Trại Mới, Xã Tân Hòa, Huyện Phú Xuyên",
                province="Hà Nội",
                district="Phú Xuyên",
                latitude=20.30,
                longitude=105.70,
                farm_type=FarmType.BROILER,
                status=FarmStatus.SUSPECT,
                phone="0912345680",
            ),
        ]
        for farm in farms:
            db.add(farm)

    # --- Dịch bệnh ---
    if db.query(Outbreak).count() == 0:
        outbreak1 = Outbreak(
            disease=Disease.NEWTONS,
            symptom="Tràn dịch ở hốc mắt, chảy máu mũi",
            detected_at=datetime(2024, 1, 15, tzinfo=timezone.utc),
            status=OutbreakStatus.CONFIRMED,
            description="Dịch Newcastle tại trang trại broiler.",
            farm_id=farms[0].id,
        )
        db.add(outbreak1)

        outbreak2 = Outbreak(
            disease=Disease.GUMBOTS,
            symptom="Tràn dịch ở cổ, tiêu chảy",
            detected_at=datetime(2024, 2, 1, tzinfo=timezone.utc),
            status=OutbreakStatus.MONITORING,
            description="Dịch Gumboro tại trang trại layer.",
            farm_id=farms[1].id,
        )
        db.add(outbreak2)

    # --- Cảnh báo ---
    if db.query(Alert).count() == 0:
        alert1 = Alert(
            severity=AlertSeverity.HIGH,
            message="Cảnh báo dịch Newcastle tại trang trại Nguyễn Văn A.",
            status=AlertStatus.PENDING,
            outbreak_id=outbreak1.id,
            farm_id=farms[0].id,
        )
        db.add(alert1)

        alert2 = Alert(
            severity=AlertSeverity.MEDIUM,
            message="Cảnh báo dịch Gumboro tại trang trại Trần Thị B.",
            status=AlertStatus.PENDING,
            outbreak_id=outbreak2.id,
            farm_id=farms[1].id,
        )
        db.add(alert2)

    db.commit()


__all__ = ["seed"]