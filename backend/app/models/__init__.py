"""Database models package."""

# Import all models to ensure they are registered with SQLAlchemy
from app.models.enums import (  # noqa: F401
    PoultryTypeEnum,
    OutbreakStatusEnum,
    SeverityLevelEnum,
    RiskLevelEnum,
    AlertStatusEnum,
)
from app.models.user import User  # noqa: F401
from app.models.farm import Farm  # noqa: F401
from app.models.outbreak import Outbreak  # noqa: F401
from app.models.alert import Alert  # noqa: F401
from app.models.base import Base  # noqa: F401

__all__ = [
    "Base",
    "User",
    "Farm",
    "Outbreak",
    "Alert",
    "PoultryTypeEnum",
    "OutbreakStatusEnum",
    "SeverityLevelEnum",
    "RiskLevelEnum",
    "AlertStatusEnum",
]