"""Model trang trại."""
import uuid

from geoalchemy2 import Geometry
from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, IdTimestampMixin
from app.models.enums import PoultryType, pg_enum


class Farm(IdTimestampMixin, Base):
    __tablename__ = "farms"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    owner_name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str] = mapped_column(String(20), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    province: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    district: Mapped[str | None] = mapped_column(String(100), nullable=True)
    commune: Mapped[str | None] = mapped_column(String(100), nullable=True)
    hamlet: Mapped[str | None] = mapped_column(String(150), nullable=True)
    poultry_type: Mapped[PoultryType] = mapped_column(
        pg_enum(PoultryType, "poultry_type"), default=PoultryType.CHICKEN, nullable=False
    )
    capacity: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true", nullable=False)
    # Tài khoản được xem và xác nhận cảnh báo của trang trại này. owner_name ở trên chỉ là tên để liên hệ.
    owner_user_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    location = mapped_column(
        Geometry(geometry_type="POINT", srid=4326, spatial_index=True), nullable=True
    )


__all__ = ["Farm"]
