"""Model Cảnh báo với SQLAlchemy 2.0, GeoAlchemy2 và Foreign Keys."""

from datetime import datetime, timezone

import uuid
from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, BaseModel
from app.models.enums import AlertStatusEnum, RiskLevelEnum


class Alert(Base):
    """Cảnh báo về ổ dịch."""

    __tablename__ = "alerts"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, unique=True, index=True, nullable=False, default=lambda: str(uuid.uuid4())
    )
    """Mã định danh cảnh báo (UUID)."""

    outbreak_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("outbreaks.id"), nullable=False, index=True
    )
    """ID ổ dịch liên quan."""

    farm_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("farms.id", ondelete="CASCADE"), nullable=True
    )
    """ID trang trại nhận cảnh báo (nếu có)."""

    distance_km: Mapped[float] = mapped_column(Float, default=0.0, server_default="0.0", nullable=False)
    """Khoảng cách từ ổ dịch đến trang trại tính bằng km."""

    risk_level: Mapped[RiskLevelEnum | str] = mapped_column(
        String(50), index=True, nullable=False
    )
    """Mức độ rủi ro (very_high, high, medium, low)."""

    message: Mapped[str] = mapped_column(Text, nullable=False)
    """Nội dung thông báo."""

    status: Mapped[AlertStatusEnum | str] = mapped_column(
        ENUM(AlertStatusEnum, name="alert_status"),
        default=AlertStatusEnum.PENDING,
        nullable=False,
    )
    """Trạng thái cảnh báo."""

    sent_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    """Thời điểm gửi cảnh báo."""

    acknowledged_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    """Thời điểm nhận cảnh báo."""

    created_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=True
    )
    """Thời điểm tạo cảnh báo."""

    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=True,
    )
    """Thời điểm cập nhật."""

    # Relationship với Outbreak
    outbreak: Mapped["Outbreak"] = relationship(
        "Outbreak",
        back_populates="alerts",
        lazy="selectin",
    )

    # Relationship với Farm (nếu có)
    farm: Mapped["Farm"] = relationship(
        "Farm",
        uselist=False,
        lazy="joined",
    )

    __table_args__ = (
        UniqueConstraint("outbreak_id", "farm_id", name="uq_alert_outbreak_farm"),
    )


__all__ = ["Alert"]
