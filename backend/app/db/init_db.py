"""Khởi tạo kết nối và cơ sở dữ liệu."""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.core.database import Base

from app.models import farm, outbreak, alert, user

engine = create_engine(
    settings.database_url,
    pool_size=settings.database_pool_size,
    max_overflow=settings.database_max_overflow,
    pool_pre_ping=settings.database_pool_pre_ping,
    echo=settings.database_echo,
)

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


def get_db():
    """Lấy phiên làm việc với cơ sở dữ liệu."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Xóa toàn bộ dữ liệu và tạo lại schema."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


__all__ = ["engine", "SessionLocal", "get_db", "init_db"]