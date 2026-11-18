"""Model cảnh báo."""
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, IdTimestampMixin
from app.models.enums import AlertStatus, RiskLevel, pg_enum


class Alert(IdTimestampMixin, Base):
    __tablename__ = "alerts"
    __table_args__ = (UniqueConstraint("outbreak_id", "farm_id", name="uq_alert_outbreak_farm"),)

    outbreak_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("outbreaks.id", ondelete="CASCADE"), nullable=False, index=True
    )
    farm_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("farms.id", ondelete="CASCADE"), nullable=False, index=True
    )
    distance_km: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    risk_level: Mapped[RiskLevel] = mapped_column(pg_enum(RiskLevel, "risk_level"), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    # Các yếu tố đã dùng để xác định risk_level, để người đọc kiểm tra được vì sao ra mức đó
    risk_basis: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[AlertStatus] = mapped_column(
        pg_enum(AlertStatus, "alert_status"), default=AlertStatus.PENDING, nullable=False, index=True
    )
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


__all__ = ["Alert"]
