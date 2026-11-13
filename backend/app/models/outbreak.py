"""Model Ổ dịch với SQLAlchemy 2.0 và GeoAlchemy2."""

from datetime import datetime, timezone

import uuid
from geoalchemy2 import Geometry
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func, text
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, BaseModel
from app.models.enums import (
    OutbreakStatusEnum,
    SeverityLevelEnum,
)


class Outbreak(Base):
    """Ổ dịch gia cầm."""

    __tablename__ = "outbreaks"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, unique=True, index=True, nullable=False, default=lambda: str(uuid.uuid4())
    )
    """Mã định danh ổ dịch (UUID)."""

    virus_type: Mapped[str] = mapped_column(String(255), nullable=False)
    """Loại virus (ví dụ: AIV H5N1, NDV, IBV...)."""

    province: Mapped[str] = mapped_column(String(100), nullable=False)
    """Tỉnh/Thành phố."""

    district: Mapped[str] = mapped_column(String(100), nullable=True)
    """Quận/Huyện (nếu có)."""

    location: Mapped[str | None] = mapped_column(
        Geometry(geometry_type="POINT", srid=4326),
        nullable=True,
    )
    """Định dạng GeoAlchemy2 POINT('SRID=4326;POINT(lon lat)')."""

    address: Mapped[str] = mapped_column(Text, nullable=False)
    """Địa chỉ chi tiết ổ dịch."""

    cases_count: Mapped[int] = mapped_column(
        Integer, default=0, server_default="0", nullable=False
    )
    """Số lượng ca bệnh đã ghi nhận. Phải >= 0."""

    status: Mapped[OutbreakStatusEnum | str] = mapped_column(
        ENUM(OutbreakStatusEnum, name="outbreak_status"),
        nullable=False,
    )
    """Trạng thái ổ dịch."""

    severity: Mapped[SeverityLevelEnum | str] = mapped_column(
        ENUM(SeverityLevelEnum, name="severity_level"),
        nullable=False,
    )
    """Mức độ nghiêm trọng."""

    reported_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    """Thời điểm báo cáo ổ dịch."""

    created_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=True
    )
    """Thời điểm tạo."""

    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=True,
    )
    """Thời điểm cập nhật."""

    # Relationship với Farm (trang trại liên quan)
    farm: Mapped["Farm"] = relationship(
        "Farm",
        back_populates="outbreaks",
        uselist=False,
    )

    # Relationship với Alert (các cảnh báo phát ra từ ổ dịch này)
    alerts: Mapped[list["Alert"]] = relationship(
        "Alert",
        back_populates="outbreak",
        lazy="selectin",
    )


__all__ = ["Outbreak"]
