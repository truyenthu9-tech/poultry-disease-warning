"""Hồ sơ đăng ký trang trại chờ cán bộ thú y xét duyệt."""
import uuid
from datetime import datetime

from geoalchemy2 import Geometry
from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, IdTimestampMixin
from app.models.enums import PoultryType, pg_enum


class FarmRegistration(IdTimestampMixin, Base):
    __tablename__ = "farm_registrations"
    __table_args__ = (
        CheckConstraint("status IN ('pending', 'approved', 'rejected')", name="ck_farm_registration_status"),
        CheckConstraint("cases_count > 0", name="ck_farm_registration_cases_positive"),
        UniqueConstraint("farm_id", name="uq_farm_registrations_farm_id"),
        UniqueConstraint("outbreak_id", name="uq_farm_registrations_outbreak_id"),
    )

    submitted_by_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(String(20), default="pending", server_default="pending", nullable=False, index=True)

    farm_name: Mapped[str] = mapped_column(String(255), nullable=False)
    owner_name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str] = mapped_column(String(20), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    province: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    district: Mapped[str | None] = mapped_column(String(100), nullable=True)
    commune: Mapped[str | None] = mapped_column(String(100), nullable=True)
    hamlet: Mapped[str | None] = mapped_column(String(150), nullable=True)
    poultry_type: Mapped[PoultryType] = mapped_column(
        pg_enum(PoultryType, "poultry_type"), nullable=False
    )
    capacity: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)
    location = mapped_column(Geometry(geometry_type="POINT", srid=4326, spatial_index=False), nullable=False)

    # Giữ các trường cũ để đọc hồ sơ lịch sử; báo cáo mới dùng OutbreakReport riêng.
    virus_type: Mapped[str | None] = mapped_column(String(255), nullable=True)
    disease_started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cases_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    disease_description: Mapped[str | None] = mapped_column(Text, nullable=True)

    reviewed_by_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    review_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    farm_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("farms.id", ondelete="SET NULL"), nullable=True
    )
    outbreak_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("outbreaks.id", ondelete="SET NULL"), nullable=True
    )


__all__ = ["FarmRegistration"]
