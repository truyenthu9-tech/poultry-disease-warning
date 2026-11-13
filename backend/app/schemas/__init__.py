"""Pydantic schemas package."""

# Common schemas
from app.schemas.common import (  # noqa: F401
    MessageResponse,
    PaginatedResponse,
    ErrorResponse,
    ValidationErrorResponse,
)

# User schemas
from app.schemas.user import (  # noqa: F401
    UserBase,
    UserCreate,
    UserUpdate,
    UserResponse,
    UserInDB,
    Token,
    TokenPayload,
)

# Farm schemas
from app.schemas.farm import (  # noqa: F401
    FarmBase,
    FarmCreate,
    FarmUpdate,
    FarmResponse,
    FarmInDB,
    FarmNearbyQuery,
    FarmNearbyResponse,
)

# Outbreak schemas
from app.schemas.outbreak import (  # noqa: F401
    OutbreakBase,
    OutbreakCreate,
    OutbreakUpdate,
    OutbreakResponse,
    OutbreakInDB,
    OutbreakNearbyFarmsResponse,
)

# Alert schemas
from app.schemas.alert import (  # noqa: F401
    AlertBase,
    AlertCreate,
    AlertUpdate,
    AlertResponse,
    AlertInDB,
    AlertAcknowledge,
    UserAlertsResponse,
)

# Location schemas
from app.schemas.location import (  # noqa: F401
    Location,
)

__all__ = [
    # Common
    "MessageResponse",
    "PaginatedResponse",
    "ErrorResponse",
    "ValidationErrorResponse",
    # User
    "UserBase",
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    "UserInDB",
    "Token",
    "TokenPayload",
    # Farm
    "FarmBase",
    "FarmCreate",
    "FarmUpdate",
    "FarmResponse",
    "FarmInDB",
    "FarmNearbyQuery",
    "FarmNearbyResponse",
    # Outbreak
    "OutbreakBase",
    "OutbreakCreate",
    "OutbreakUpdate",
    "OutbreakResponse",
    "OutbreakInDB",
    "OutbreakNearbyFarmsResponse",
    # Alert
    "AlertBase",
    "AlertCreate",
    "AlertUpdate",
    "AlertResponse",
    "AlertInDB",
    "AlertAcknowledge",
    "UserAlertsResponse",
    # Location
    "Location",
]