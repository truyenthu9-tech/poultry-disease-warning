"""Migration khởi tạo: users, farms, outbreaks, alerts + enum Postgres + PostGIS.

Revision ID: ae01c4d0b231
Revises:
"""
import sqlalchemy as sa
from alembic import op
from geoalchemy2 import Geometry
from sqlalchemy.dialects import postgresql as pg

revision = "ae01c4d0b231"
down_revision = None
branch_labels = None
depends_on = None


def _enum(name: str, *values: str) -> pg.ENUM:
    return pg.ENUM(*values, name=name, create_type=False)


user_role = _enum("user_role", "admin", "vet_officer", "farm_owner", "user")
poultry_type = _enum("poultry_type", "chicken", "duck", "muscovy", "quail", "other")
outbreak_status = _enum("outbreak_status", "active", "contained", "closed")
severity_level = _enum("severity_level", "low", "medium", "high", "critical")
risk_level = _enum("risk_level", "low", "medium", "high", "critical")
alert_status = _enum("alert_status", "pending", "sent", "failed", "acknowledged")

ALL_ENUMS = [user_role, poultry_type, outbreak_status, severity_level, risk_level, alert_status]


def _ts(name: str) -> sa.Column:
    return sa.Column(name, sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now())


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")
    for e in ALL_ENUMS:
        e.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "users",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("password", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("role", user_role, nullable=False),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        _ts("created_at"),
        _ts("updated_at"),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "farms",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("owner_name", sa.String(255), nullable=False),
        sa.Column("phone", sa.String(20), nullable=False),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("address", sa.Text, nullable=True),
        sa.Column("province", sa.String(100), nullable=False),
        sa.Column("district", sa.String(100), nullable=True),
        sa.Column("poultry_type", poultry_type, nullable=False),
        sa.Column("capacity", sa.Integer, nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column("location", Geometry("POINT", srid=4326, spatial_index=False), nullable=True),
        _ts("created_at"),
        _ts("updated_at"),
    )
    op.create_index("ix_farms_province", "farms", ["province"])
    op.create_index("idx_farms_location", "farms", ["location"], postgresql_using="gist")
    op.execute("CREATE INDEX idx_farms_location_geog ON farms USING GIST ((location::geography))")

    op.create_table(
        "outbreaks",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
        sa.Column("virus_type", sa.String(255), nullable=False),
        sa.Column("province", sa.String(100), nullable=False),
        sa.Column("district", sa.String(100), nullable=True),
        sa.Column("address", sa.Text, nullable=True),
        sa.Column("location", Geometry("POINT", srid=4326, spatial_index=False), nullable=True),
        sa.Column("cases_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("status", outbreak_status, nullable=False),
        sa.Column("severity", severity_level, nullable=False),
        sa.Column("radius_km", sa.Float, nullable=False, server_default="5"),
        sa.Column("reported_date", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        _ts("created_at"),
        _ts("updated_at"),
    )
    op.create_index("ix_outbreaks_virus_type", "outbreaks", ["virus_type"])
    op.create_index("ix_outbreaks_status", "outbreaks", ["status"])
    op.create_index("idx_outbreaks_location", "outbreaks", ["location"], postgresql_using="gist")

    op.create_table(
        "alerts",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
        sa.Column("outbreak_id", pg.UUID(as_uuid=True), sa.ForeignKey("outbreaks.id", ondelete="CASCADE"), nullable=False),
        sa.Column("farm_id", pg.UUID(as_uuid=True), sa.ForeignKey("farms.id", ondelete="CASCADE"), nullable=False),
        sa.Column("distance_km", sa.Float, nullable=False, server_default="0"),
        sa.Column("risk_level", risk_level, nullable=False),
        sa.Column("message", sa.Text, nullable=False),
        sa.Column("status", alert_status, nullable=False, server_default="pending"),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        _ts("created_at"),
        _ts("updated_at"),
        sa.UniqueConstraint("outbreak_id", "farm_id", name="uq_alert_outbreak_farm"),
    )
    op.create_index("ix_alerts_outbreak_id", "alerts", ["outbreak_id"])
    op.create_index("ix_alerts_farm_id", "alerts", ["farm_id"])
    op.create_index("ix_alerts_status", "alerts", ["status"])


def downgrade() -> None:
    op.drop_table("alerts")
    op.drop_table("outbreaks")
    op.drop_table("farms")
    op.drop_table("users")
    for e in reversed(ALL_ENUMS):
        e.drop(op.get_bind(), checkfirst=True)
