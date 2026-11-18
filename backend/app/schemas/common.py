"""Schema dùng chung."""
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.utils.geo import geometry_to_location


class Location(BaseModel):
    """Tọa độ địa lý: {"latitude": float, "longitude": float}."""

    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)


class ORMResponse(BaseModel):
    """Response đọc từ ORM, tự chuyển cột Geometry `location` sang JSON lat/lon."""

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="before")
    @classmethod
    def _convert_location(cls, data: Any) -> Any:
        if isinstance(data, dict) or "location" not in cls.model_fields:
            return data
        values = {name: getattr(data, name, None) for name in cls.model_fields}
        values["location"] = geometry_to_location(getattr(data, "location", None))
        return values


T = TypeVar("T")


class Page(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    page_size: int


class PaginationParams(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


class MessageResponse(BaseModel):
    message: str


__all__ = ["Location", "ORMResponse", "Page", "PaginationParams", "MessageResponse"]
