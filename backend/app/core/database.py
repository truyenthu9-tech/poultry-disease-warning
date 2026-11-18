"""Kết nối và quản lý phiên làm việc với cơ sở dữ liệu async."""
from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings


class Base(DeclarativeBase):
    """Lớp gốc của mọi model SQLAlchemy."""


engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    pool_pre_ping=True,
    echo=settings.DATABASE_ECHO,
)

async_session_maker = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def get_db() -> AsyncIterator[AsyncSession]:
    """Dependency FastAPI: trả về AsyncSession."""
    async with async_session_maker() as session:
        yield session


async def close_db() -> None:
    await engine.dispose()
