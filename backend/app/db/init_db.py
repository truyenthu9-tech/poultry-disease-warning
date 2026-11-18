"""Khởi tạo database: bật extension PostGIS."""
from sqlalchemy import text

from app.core.database import engine


async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis;"))


__all__ = ["init_db"]
