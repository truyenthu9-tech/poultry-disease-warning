"""Pydantic schemas for location data."""
from pydantic import BaseModel, Field


class Location(BaseModel):
    """Vị trí địa lý (kinh độ, vĩ độ)."""

    longitude: float = Field(
        ...,
        description="Kinh độ (range: -180.0 to 180.0).",
        ge=-180.0,
        le=180.0,
    )
    latitude: float = Field(
        ...,
        description="Vĩ độ (range: -90.0 to 90.0).",
        ge=-90.0,
        le=90.0,
    )
