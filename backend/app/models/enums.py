"""Enum dùng chung cho models và schemas."""
from enum import Enum


class PoultryType(str, Enum):
    CHICKEN = "chicken"
    DUCK = "duck"
    MUSCOVY = "muscovy"
    QUAIL = "quail"
    OTHER = "other"


class OutbreakStatus(str, Enum):
    ACTIVE = "active"
    CONTAINED = "contained"
    CLOSED = "closed"


class Severity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertStatus(str, Enum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    ACKNOWLEDGED = "acknowledged"


class UserRole(str, Enum):
    ADMIN = "admin"
    VET_OFFICER = "vet_officer"
    FARM_OWNER = "farm_owner"
    USER = "user"


class FarmRegistrationStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


# Tên cũ giữ lại để code cũ import không bị lỗi
PoultryTypeEnum = PoultryType
OutbreakStatusEnum = OutbreakStatus
SeverityLevelEnum = Severity
RiskLevelEnum = RiskLevel
AlertStatusEnum = AlertStatus


def pg_enum(enum_cls: type[Enum], name: str):
    """Tạo kiểu ENUM Postgres lưu theo value (chữ thường)."""
    from sqlalchemy import Enum as SAEnum

    return SAEnum(
        enum_cls,
        name=name,
        values_callable=lambda e: [m.value for m in e],
        create_type=False,
    )
