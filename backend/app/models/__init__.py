"""Import toàn bộ model để Alembic nhận diện."""
from app.models.base import Base  # noqa: F401
from app.models.enums import (  # noqa: F401
    AlertStatus,
    FarmRegistrationStatus,
    OutbreakStatus,
    PoultryType,
    RiskLevel,
    Severity,
    UserRole,
)
from app.models.user import User  # noqa: F401
from app.models.farm import Farm  # noqa: F401
from app.models.farm_registration import FarmRegistration  # noqa: F401
from app.models.outbreak import Outbreak  # noqa: F401
from app.models.outbreak_report import OutbreakReport  # noqa: F401
from app.models.alert import Alert  # noqa: F401

__all__ = [
    "Base", "User", "Farm", "FarmRegistration", "Outbreak", "OutbreakReport", "Alert",
    "PoultryType", "OutbreakStatus", "Severity", "RiskLevel", "AlertStatus", "UserRole",
    "FarmRegistrationStatus",
]
