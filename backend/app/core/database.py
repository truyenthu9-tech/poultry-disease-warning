"""Kết nối và quản lý phiên làm việc với cơ sở dữ liệu async."""

from datetime import datetime, timezone
from typing import AsyncIterator

from sqlalchemy import Text, select
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from .config import settings


class Base(DeclarativeBase):
    """Cội của mọi model SQLAlchemy."""


async_session_maker = async_sessionmaker(
    create_async_engine(
        settings.DATABASE_URL,
        pool_size=settings.database_pool_size,
        max_overflow=settings.database_max_overflow,
        pool_pre_ping=settings.database_pool_pre_ping,
        echo=settings.database_echo,
    ),
    expire_on_commit=False,
    class_=Base,
)


async def init_db() -> None:
    """Initialize database connection.

    Chạy SELECT 1 để test kết nối và đảm bảo engine đã khởi động đúng.
    Không chạy migration hay seed ở đây.
    """
    # Tạo engine nếu chưa được tạo (lazy initialization)
    engine = async_session_maker._async_engine
    assert engine is not None, "Engine không thể None"
    
    # Test kết nối với SELECT 1
    async with async_session_maker() as session:
        result = await session.execute(select(1))
        assert result.scalar_one() == 1, "Không thể kết nối database"


async def close_db() -> None:
    """Đóng kết nối database và dispose engine.

    Gọi ở shutdown event của FastAPI.
    """
    engine = async_session_maker._async_engine
    if engine is not None:
        await engine.dispose()


async def get_db() -> AsyncIterator[AsyncSession]:
    """Dependency FastAPI: trả về một AsyncSession (auto-close sau khi dùng)."""
    async with async_session_maker() as session:
        yield session


def now_aware() -> datetime:
    return datetime.now(timezone.utc)