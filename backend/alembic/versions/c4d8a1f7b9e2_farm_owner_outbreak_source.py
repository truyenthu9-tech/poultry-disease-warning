"""Chủ trại (tài khoản), nguồn gốc và xác nhận ổ dịch, cơ sở đánh giá của cảnh báo.

Revision ID: c4d8a1f7b9e2
Revises: ae01c4d0b231
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql as pg

revision = "c4d8a1f7b9e2"
down_revision = "ae01c4d0b231"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # farms: tài khoản sở hữu trang trại, quyết định ai được xem và xác nhận cảnh báo
    op.add_column("farms", sa.Column("owner_user_id", pg.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key(
        "fk_farms_owner_user_id_users", "farms", "users", ["owner_user_id"], ["id"], ondelete="SET NULL"
    )
    op.create_index("ix_farms_owner_user_id", "farms", ["owner_user_id"])

    # outbreaks: nguồn gốc và xác nhận. Dòng đã có coi như do cán bộ nhập tay và đã xác nhận.
    op.add_column("outbreaks", sa.Column("source", sa.String(255), nullable=False, server_default="manual"))
    op.add_column("outbreaks", sa.Column("source_url", sa.Text, nullable=True))
    op.add_column("outbreaks", sa.Column("external_id", sa.String(255), nullable=True))
    op.add_column("outbreaks", sa.Column("verified", sa.Boolean, nullable=False, server_default=sa.text("true")))
    op.add_column("outbreaks", sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("outbreaks", sa.Column("verified_by_id", pg.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key(
        "fk_outbreaks_verified_by_id_users", "outbreaks", "users", ["verified_by_id"], ["id"], ondelete="SET NULL"
    )
    op.create_unique_constraint("uq_outbreak_source_external", "outbreaks", ["source", "external_id"])

    # alerts: ghi lại cơ sở đánh giá mức nguy cơ
    op.add_column("alerts", sa.Column("risk_basis", sa.Text, nullable=True))


def downgrade() -> None:
    op.drop_column("alerts", "risk_basis")

    op.drop_constraint("uq_outbreak_source_external", "outbreaks", type_="unique")
    op.drop_constraint("fk_outbreaks_verified_by_id_users", "outbreaks", type_="foreignkey")
    for column in ("verified_by_id", "verified_at", "verified", "external_id", "source_url", "source"):
        op.drop_column("outbreaks", column)

    op.drop_index("ix_farms_owner_user_id", table_name="farms")
    op.drop_constraint("fk_farms_owner_user_id_users", "farms", type_="foreignkey")
    op.drop_column("farms", "owner_user_id")
