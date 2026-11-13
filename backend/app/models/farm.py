"""Model Trang trại với SQLAlchemy 2.0, GeoAlchemy2."""

import uuid
from datetime import datetime, timezone

from geoalchemy2 import Geometry
from sqlalchemy import Boolean, DateTime, String, Text
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, BaseModel


class Farm(Base):
    """Trang trại chăn nuôi gia cầm."""

    __tablename__ = "farms"

    id: Mapped[uuid.UUID] = mapped_column(
        uuid.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False, index=True
    )
    """Mã định danh trang trại (UUID)."""

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    """Tên trang trại."""

    owner_name: Mapped[str] = mapped_column(String(255), nullable=False)
    """Họ và tên chủ sở hữu."""

    phone: Mapped[str] = mapped_column(String(20), index=True, nullable=False)
    """Số điện thoại liên hệ."""

    poultry_type: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    """Loại gia cầm (ví dụ: broiler, layer, thả tự do, vịt, ngan)."""

    capacity: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)
    """Công suất nuôi (số lượng đầu). Phải >= 0."""

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true", nullable=False)
    """Trạng thái hoạt động."""

    location: Mapped[str | None] = mapped_column(
        Geometry(geometry_type="POINT", srid=4326),
        nullable=True,
    )
    """Định dạng GeoAlchemy2 POINT('SRID=4326;POINT(lon lat)')."""

    address: Mapped[str] = mapped_column(Text, nullable=False)
    """Địa chỉ chi tiết."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default="now()",
    )
    """Thời điểm tạo."""

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default="now()",
        onupdate="now()",
    )
    """Thời điểm cập nhật."""

    # Relationship với Outbreak (nếu trang trại liên quan đến ổ dịch)
    outbreaks: Mapped[list["Outbreak"]] = relationship(
        "Outbreak",
        back_populates="farm",
        lazy="selectin",
    )


__all__ = ["Farm"]
