"""Migration khởi tạo toàn bộ schema: farm, outbreak, alert + enum Postgres.

Chạy: alembic upgrade head
"""
import enum
import typing as t

from alembic import context
from sqlalchemy import (
    Float,
    Integer,
    Text,
    DateTime,
    Boolean,
    Text as TextType,
)
from sqlalchemy.dialects.postgresql import (
    UUID,
    Enum,
    Geometry,
    Geography,
)

from app.core.config import settings
from app.models.base import Base
from app.models.farm import Farm
from app.models.outbreak import Outbreak
from app.models.alert import Alert

revision = "ae01c4d0b231"
down_revision = None


def upgrade() -> None:
    with context.begin_transaction():
        # --- Extension PostGIS (nếu chưa có) ---
        context.run_sql("CREATE EXTENSION IF NOT EXISTS postgis")

        # --- Enum Postgres (tạo đúng kiểu ENUM, không dùng VARCHAR) ---
        context.run_sql(
            "CREATE TYPE IF NOT EXISTS poultry_poultry_type AS ENUM (%s)"
            % ", ".join("`%s`" % e.value for e in Farm.poultry_type.enum)
        )
        context.run_sql(
            "CREATE TYPE IF NOT EXISTS poultry_outbreak_status AS ENUM (%s)"
            % ", ".join("`%s`" % e.value for e in Outbreak.status.enum)
        )
        context.run_sql(
            "CREATE TYPE IF NOT EXISTS poultry_outbreak_severity AS ENUM (%s)"
            % ", ".join("`%s`" % e.value for e in Outbreak.severity.enum)
        )
        context.run_sql(
            "CREATE TYPE IF NOT EXISTS poultry_alert_risk_level AS ENUM (%s)"
            % ", ".join("`%s`" % e.value for e in Alert.risk_level.enum)
        )
        context.run_sql(
            "CREATE TYPE IF NOT EXISTS poultry_alert_status AS ENUM (%s)"
            % ", ".join("`%s`" % e.value for e in Alert.status.enum)
        )

        # --- Bảng Farm ---
        context.run_sql(
            """
            CREATE TABLE IF NOT EXISTS farm (
                id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                name TEXT NOT NULL,
                owner_name TEXT NOT NULL,
                phone TEXT NOT NULL,
                email TEXT NOT NULL,
                address TEXT,
                province TEXT NOT NULL,
                district TEXT NOT NULL,
                poultry_type poultry_poultry_type NOT NULL,
                capacity INTEGER NOT NULL,
                is_active BOOLEAN NOT NULL DEFAULT TRUE,
                location GEOGRAPHY(POINT, 4326),
                created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
            )
        """
        )
        context.run_sql(
            "CREATE INDEX IF NOT EXISTS farm_location_gist ON farm USING GIST (location)"
        )

        # --- Bảng Outbreak ---
        context.run_sql(
            """
            CREATE TABLE IF NOT EXISTS outbreak (
                id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                virus_type TEXT NOT NULL,
                province TEXT NOT NULL,
                district TEXT NOT NULL,
                location GEOGRAPHY(POINT, 4326),
                cases_count INTEGER NOT NULL,
                status poultry_outbreak_status NOT NULL,
                severity poultry_outbreak_severity NOT NULL,
                radius_km FLOAT NOT NULL DEFAULT %(radius)s,
                reported_date TIMESTAMPTZ NOT NULL DEFAULT now(),
                created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
            )
        """
        )
        context.run_sql(
            "CREATE INDEX IF NOT EXISTS outbreak_status_idx ON outbreak (status)"
        )
        context.run_sql(
            "CREATE INDEX IF NOT EXISTS outbreak_virus_type_idx ON outbreak (virus_type)"
        )
        context.run_sql(
            "CREATE INDEX IF NOT EXISTS outbreak_location_gist ON outbreak USING GIST (location)"
        )

        # --- Bảng Alert ---
        context.run_sql(
            """
            CREATE TABLE IF NOT EXISTS alert (
                id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                outbreak_id UUID NOT NULL REFERENCES outbreak (id) ON DELETE CASCADE,
                farm_id UUID NOT NULL REFERENCES farm (id) ON DELETE CASCADE,
                distance_km FLOAT NOT NULL,
                risk_level poultry_alert_risk_level NOT NULL,
                message TEXT NOT NULL,
                status poultry_alert_status NOT NULL DEFAULT 'PENDING',
                sent_at TIMESTAMPTZ,
                created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                UNIQUE (outbreak_id, farm_id)
            )
        """
        )
        context.run_sql(
            "CREATE INDEX IF NOT EXISTS alert_outbreak_idx ON alert (outbreak_id)"
        )
        context.run_sql(
            "CREATE INDEX IF NOT EXISTS alert_farm_idx ON alert (farm_id)"
        )


def downgrade() -> None:
    with context.begin_transaction():
        context.run_sql("DROP TABLE IF EXISTS alert")
        context.run_sql("DROP TABLE IF EXISTS outbreak")
        context.run_sql("DROP TABLE IF EXISTS farm")
        context.run_sql("DROP INDEX IF EXISTS alert_farm_idx")
        context.run_sql("DROP INDEX IF EXISTS alert_outbreak_idx")
        context.run_sql("DROP INDEX IF EXISTS outbreak_location_gist")
        context.run_sql("DROP INDEX IF EXISTS outbreak_virus_type_idx")
        context.run_sql("DROP INDEX IF EXISTS outbreak_status_idx")
        context.run_sql("DROP INDEX IF EXISTS farm_location_gist")
        context.run_sql("DROP TYPE IF EXISTS poultry_alert_status")
        context.run_sql("DROP TYPE IF EXISTS poultry_alert_risk_level")
        context.run_sql("DROP TYPE IF EXISTS poultry_outbreak_severity")
        context.run_sql("DROP TYPE IF EXISTS poultry_outbreak_status")
        context.run_sql("DROP TYPE IF EXISTS poultry_poultry_type")
        context.run_sql("DROP EXTENSION IF EXISTS postgis")