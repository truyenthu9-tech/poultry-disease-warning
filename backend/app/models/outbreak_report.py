"""Báo cáo dịch do người dùng gửi, chỉ tạo ổ dịch sau khi cán bộ duyệt."""
import uuid
from datetime import datetime

from geoalchemy2 import Geometry
from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, IdTimestampMixin


class OutbreakReport(IdTimestampMixin, Base):
    __tablename__ = "outbreak_reports"
    __table_args__ = (
        CheckConstraint("status IN ('pending', 'approved', 'rejected')", name="ck_outbreak_report_status"),
        CheckConstraint("cases_count > 0", name="ck_outbreak_report_cases_positive"),
        UniqueConstraint("outbreak_id", name="uq_outbreak_reports_outbreak_id"),
    )

    submitted_by_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(String(20), default="pending", server_default="pending", nullable=False, index=True)
    reporter_name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str] = mapped_column(String(20), nullable=False)
    virus_type: Mapped[str] = mapped_column(String(255), nullable=False)
    province: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    district: Mapped[str | None] = mapped_column(String(100), nullable=True)
    commune: Mapped[str | None] = mapped_column(String(100), nullable=True)
    hamlet: Mapped[str | None] = mapped_column(String(150), nullable=True)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    location = mapped_column(Geometry(geometry_type="POINT", srid=4326), nullable=False)
    onset_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    cases_count: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    reviewed_by_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    review_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    outbreak_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("outbreaks.id", ondelete="SET NULL"), nullable=True
    )


__all__ = ["OutbreakReport"]
