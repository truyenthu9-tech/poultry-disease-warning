"""Enum PostgreSQL cho các mô hình."""

from enum import Enum
from sqlalchemy import Enum as SA_Enum
from sqlalchemy.dialects.postgresql import ENUM


class PoultryTypeEnum(SA_Enum):
    """Loại gia cầm."""
    
    name = "poultry_type"
    
    BROIILER = "broiler"
    LAYER = "layer"
    FREE_RANGE = "free_range"
    DUCK = "duck"
    GOOSE = "goose"
    TURKEY = "turkey"


class OutbreakStatusEnum(SA_Enum):
    """Trạng thái ổ dịch."""
    
    name = "outbreak_status"
    
    SUSPECTED = "suspected"
    CONFIRMED = "confirmed"
    INVESTIGATING = "investigating"
    RESOLVED = "resolved"


class SeverityLevelEnum(SA_Enum):
    """Mức độ nghiêm trọng."""
    
    name = "severity_level"
    
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class RiskLevelEnum(SA_Enum):
    """Mức độ rủi ro."""
    
    name = "risk_level"
    
    VERY_HIGH = "very_high"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class AlertStatusEnum(SA_Enum):
    """Trạng thái cảnh báo."""
    
    name = "alert_status"
    
    PENDING = "pending"
    SENT = "sent"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"


class UserRole(str, Enum):
    """Vai trò tài khoản."""
    
    ADMIN = "admin"
    USER = "user"
    VET_OFFICER = "vet_officer"
    FARM_OWNER = "farm_owner"


__all__ = [
    "PoultryTypeEnum",
    "OutbreakStatusEnum", 
    "SeverityLevelEnum",
    "RiskLevelEnum",
    "AlertStatusEnum",
    "UserRole",
]
