"""Model ổ dịch."""
import uuid
from datetime import datetime

from geoalchemy2 import Geometry
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.config import settings
from app.models.base import Base, IdTimestampMixin
from app.models.enums import OutbreakStatus, Severity, pg_enum


class Outbreak(IdTimestampMixin, Base):
    __tablename__ = "outbreaks"
    # Mỗi bản ghi nhập từ một nguồn bên ngoài chỉ được lưu một lần
    __table_args__ = (UniqueConstraint("source", "external_id", name="uq_outbreak_source_external"),)

    virus_type: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    province: Mapped[str] = mapped_column(String(100), nullable=False)
    district: Mapped[str | None] = mapped_column(String(100), nullable=True)
    commune: Mapped[str | None] = mapped_column(String(100), nullable=True)
    hamlet: Mapped[str | None] = mapped_column(String(150), nullable=True)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    location = mapped_column(
        Geometry(geometry_type="POINT", srid=4326, spatial_index=True), nullable=True
    )
    cases_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)
    status: Mapped[OutbreakStatus] = mapped_column(
        pg_enum(OutbreakStatus, "outbreak_status"),
        default=OutbreakStatus.ACTIVE,
        nullable=False,
        index=True,
    )
    severity: Mapped[Severity] = mapped_column(
        pg_enum(Severity, "severity_level"), default=Severity.MEDIUM, nullable=False
    )
    radius_km: Mapped[float] = mapped_column(
        Float, default=lambda: settings.DEFAULT_ALERT_RADIUS_KM, nullable=False
    )
    reported_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    # Thời điểm người báo cáo ghi nhận bệnh bắt đầu; có thể khác ngày nhập dữ liệu.
    onset_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    # Nguồn gốc và trạng thái xác nhận. Ổ dịch cán bộ nhập tay được coi là đã xác nhận,
    # ổ dịch nhập từ nguồn bên ngoài phải được cán bộ xác nhận trước khi tạo được cảnh báo.
    source: Mapped[str] = mapped_column(String(255), default="manual", server_default="manual", nullable=False)
    source_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    external_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    verified: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true", nullable=False)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    verified_by_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )


__all__ = ["Outbreak"]
