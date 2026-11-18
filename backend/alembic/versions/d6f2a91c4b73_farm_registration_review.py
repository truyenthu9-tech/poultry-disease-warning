"""Đăng ký trại và báo cáo dịch chờ cán bộ thú y xác nhận.

Revision ID: d6f2a91c4b73
Revises: c4d8a1f7b9e2
"""
import sqlalchemy as sa
from alembic import op
from geoalchemy2 import Geometry
from sqlalchemy.dialects import postgresql as pg

revision = "d6f2a91c4b73"
down_revision = "c4d8a1f7b9e2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("outbreaks", sa.Column("onset_date", sa.DateTime(timezone=True), nullable=True))

    op.create_table(
        "farm_registrations",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("submitted_by_id", pg.UUID(as_uuid=True), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="pending"),
        sa.Column("farm_name", sa.String(length=255), nullable=False),
        sa.Column("owner_name", sa.String(length=255), nullable=False),
        sa.Column("phone", sa.String(length=20), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("address", sa.Text(), nullable=True),
        sa.Column("province", sa.String(length=100), nullable=False),
        sa.Column("district", sa.String(length=100), nullable=True),
        sa.Column(
            "poultry_type",
            pg.ENUM(name="poultry_type", create_type=False),
            nullable=False,
        ),
        sa.Column("capacity", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("location", Geometry(geometry_type="POINT", srid=4326), nullable=False),
        sa.Column("virus_type", sa.String(length=255), nullable=False),
        sa.Column("disease_started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("cases_count", sa.Integer(), nullable=False),
        sa.Column("disease_description", sa.Text(), nullable=True),
        sa.Column("reviewed_by_id", pg.UUID(as_uuid=True), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("review_note", sa.Text(), nullable=True),
        sa.Column("farm_id", pg.UUID(as_uuid=True), nullable=True),
        sa.Column("outbreak_id", pg.UUID(as_uuid=True), nullable=True),
        sa.CheckConstraint(
            "status IN ('pending', 'approved', 'rejected')", name="ck_farm_registration_status"
        ),
        sa.CheckConstraint("cases_count > 0", name="ck_farm_registration_cases_positive"),
        sa.ForeignKeyConstraint(["submitted_by_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["reviewed_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["farm_id"], ["farms.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["outbreak_id"], ["outbreaks.id"], ondelete="SET NULL"),
        sa.UniqueConstraint("farm_id", name="uq_farm_registrations_farm_id"),
        sa.UniqueConstraint("outbreak_id", name="uq_farm_registrations_outbreak_id"),
    )
    op.create_index("ix_farm_registrations_submitted_by_id", "farm_registrations", ["submitted_by_id"])
    op.create_index("ix_farm_registrations_status", "farm_registrations", ["status"])
    op.create_index("ix_farm_registrations_province", "farm_registrations", ["province"])


def downgrade() -> None:
    op.drop_index("ix_farm_registrations_province", table_name="farm_registrations")
    op.drop_index("ix_farm_registrations_status", table_name="farm_registrations")
    op.drop_index("ix_farm_registrations_submitted_by_id", table_name="farm_registrations")
    op.drop_table("farm_registrations")
    op.drop_column("outbreaks", "onset_date")
