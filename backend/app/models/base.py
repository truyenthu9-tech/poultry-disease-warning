"""Model cơ sở chung: UUID tự tăng, timestamp tự động, chuyển đổi sang dict."""

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import func
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import CHAR, SMALLINT, TEXT, TIMESTAMP

from app.core.database import Base as SqlAlchemyBase, now_aware


class Base(SqlAlchemyBase):
    """Mixin: cột id (UUID) và cột timestamp tự động."""

    id: Mapped[uuid.UUID] = mapped_column(
        uuid.UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


class BaseModel(Base):
    """Mixin dùng chung cho các model nghiệp vụ."""

    def to_dict(self) -> dict[str, Any]:
        """Xuất toàn bộ thuộc tính (loại bỏ trạng thái SQLAlchemy)."""
        data = vars(self).copy()
        data.pop("_sa_instance_state", None)
        return {k: v for k, v in data.items() if not k.startswith("_")}

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} {self.id}>"