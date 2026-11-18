"""Thêm xã và thôn vào địa chỉ trang trại, hồ sơ và ổ dịch.

Revision ID: e18a73f0b642
Revises: d6f2a91c4b73
"""
import sqlalchemy as sa
from alembic import op

revision = "e18a73f0b642"
down_revision = "d6f2a91c4b73"
branch_labels = None
depends_on = None


def upgrade() -> None:
    for table in ("farms", "farm_registrations", "outbreaks"):
        op.add_column(table, sa.Column("commune", sa.String(length=100), nullable=True))
        op.add_column(table, sa.Column("hamlet", sa.String(length=150), nullable=True))


def downgrade() -> None:
    for table in ("outbreaks", "farm_registrations", "farms"):
        op.drop_column(table, "hamlet")
        op.drop_column(table, "commune")
