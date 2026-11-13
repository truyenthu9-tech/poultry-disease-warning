"""Cấu hình ứng dụng (đọc từ biến môi trường, fallback bằng giá trị mặc định)."""

from typing import Optional
from pydantic import Field as PydanticField
from pydantic import field_validator

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- Thông tin chung ---
    app_name: str = PydanticField(default="Poultry Disease Warning System")
    debug: bool = PydanticField(default=False)
    environment: str = PydanticField(default="development")
    
    # API v1 path
    API_V1_STR: str = PydanticField(default="/api/v1")
    
    # Project metadata (for OpenAPI)
    PROJECT_NAME: str = PydanticField(default="Poultry Disease Warning System")
    VERSION: str = PydanticField(default="0.1.0")
    DESCRIPTION: str = PydanticField(default="Hệ thống cảnh báo dịch bệnh gia cầm")

    # --- Database ---
    DATABASE_URL: str = PydanticField(
        default="postgresql+asyncpg://postgres@localhost:5432/poultry_disease_warning",
        description="Connection string cho database production (PostgreSQL/PostGIS)"
    )
    TEST_DATABASE_URL: str = PydanticField(
        default="postgresql+asyncpg://postgres@localhost:5432/poultry_disease_test",
        description="Connection string cho database test (cho pytest)"
    )
    database_pool_size: int = PydanticField(default=10)
    database_max_overflow: int = PydanticField(default=5)
    database_pool_pre_ping: bool = PydanticField(default=True)
    database_echo: bool = PydanticField(default=False)

    # --- Cảnh báo geospatial ---
    DEFAULT_ALERT_RADIUS_KM: float = PydanticField(
        default=5.0,
        description="Bán kính mặc định (km) để tính cảnh báo dịch bệnh"
    )

    # --- JWT ---
    JWT_SECRET_KEY: str = PydanticField(default="super-secret-key-change-me-now")
    JWT_ALGORITHM: str = PydanticField(default="HS256")
    JWT_TOKEN_EXPIRE_MINUTES: int = PydanticField(default=60)

    # --- Services ---
    NOTIFICATION_EMAIL: str = PydanticField(default="alerts@poultry-warning.local")
    NOTIFICATION_SMTP_HOST: str = PydanticField(default="localhost")
    NOTIFICATION_SMTP_PORT: int = PydanticField(default=587)
    CRAWLER_ENABLED: bool = PydanticField(default=True)
    CRAWLER_URL: str = PydanticField(default="https://example.gov.vn")
    CRAWLER_INTERVAL_HOURS: int = PydanticField(default=24)

    # --- CORS ---
    CORS_ORIGINS: str = PydanticField(default="http://localhost:5173")
    BACKEND_CORS_ORIGINS: str = PydanticField(default="http://localhost:5173")

    @field_validator("CORS_ORIGINS", "BACKEND_CORS_ORIGINS")
    @classmethod
    def validate_cors_origins(cls, v):
        origins = [o.strip() for o in v.split(",") if o.strip()]
        return ",".join(origins)

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]


settings = Settings()