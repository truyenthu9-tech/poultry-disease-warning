"""Tách báo cáo dịch bệnh khỏi hồ sơ đăng ký trang trại.

Revision ID: f52ce109bc71
Revises: e18a73f0b642
"""
import sqlalchemy as sa
from alembic import op
from geoalchemy2 import Geometry
from sqlalchemy.dialects import postgresql as pg

revision = "f52ce109bc71"
down_revision = "e18a73f0b642"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column("farm_registrations", "virus_type", existing_type=sa.String(length=255), nullable=True)
    op.alter_column("farm_registrations", "disease_started_at", existing_type=sa.DateTime(timezone=True), nullable=True)
    op.alter_column("farm_registrations", "cases_count", existing_type=sa.Integer(), nullable=True)

    op.create_table(
        "outbreak_reports",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("submitted_by_id", pg.UUID(as_uuid=True), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="pending"),
        sa.Column("reporter_name", sa.String(length=255), nullable=False),
        sa.Column("phone", sa.String(length=20), nullable=False),
        sa.Column("virus_type", sa.String(length=255), nullable=False),
        sa.Column("province", sa.String(length=100), nullable=False),
        sa.Column("district", sa.String(length=100), nullable=True),
        sa.Column("commune", sa.String(length=100), nullable=True),
        sa.Column("hamlet", sa.String(length=150), nullable=True),
        sa.Column("address", sa.Text(), nullable=True),
        sa.Column("location", Geometry(geometry_type="POINT", srid=4326), nullable=False),
        sa.Column("onset_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("cases_count", sa.Integer(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("reviewed_by_id", pg.UUID(as_uuid=True), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("review_note", sa.Text(), nullable=True),
        sa.Column("outbreak_id", pg.UUID(as_uuid=True), nullable=True),
        sa.CheckConstraint("status IN ('pending', 'approved', 'rejected')", name="ck_outbreak_report_status"),
        sa.CheckConstraint("cases_count > 0", name="ck_outbreak_report_cases_positive"),
        sa.ForeignKeyConstraint(["submitted_by_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["reviewed_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["outbreak_id"], ["outbreaks.id"], ondelete="SET NULL"),
        sa.UniqueConstraint("outbreak_id", name="uq_outbreak_reports_outbreak_id"),
    )
    op.create_index("ix_outbreak_reports_submitted_by_id", "outbreak_reports", ["submitted_by_id"])
    op.create_index("ix_outbreak_reports_status", "outbreak_reports", ["status"])
    op.create_index("ix_outbreak_reports_province", "outbreak_reports", ["province"])


def downgrade() -> None:
    op.drop_index("ix_outbreak_reports_province", table_name="outbreak_reports")
    op.drop_index("ix_outbreak_reports_status", table_name="outbreak_reports")
    op.drop_index("ix_outbreak_reports_submitted_by_id", table_name="outbreak_reports")
    op.drop_table("outbreak_reports")
    op.alter_column("farm_registrations", "cases_count", existing_type=sa.Integer(), nullable=False)
    op.alter_column("farm_registrations", "disease_started_at", existing_type=sa.DateTime(timezone=True), nullable=False)
    op.alter_column("farm_registrations", "virus_type", existing_type=sa.String(length=255), nullable=False)
