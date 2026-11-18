"""Cấu hình ứng dụng (đọc từ biến môi trường hoặc file .env)."""
import logging
import secrets
from pathlib import Path
from urllib.parse import urlparse

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_BACKEND_DIR = Path(__file__).resolve().parents[2]
_ROOT_DIR = _BACKEND_DIR.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(str(_ROOT_DIR / ".env"), str(_BACKEND_DIR / ".env")),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- Thông tin chung ---
    APP_ENV: str = "development"  # đặt production khi triển khai thật
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Poultry Disease Warning System"
    VERSION: str = "0.1.0"
    DESCRIPTION: str = "Hệ thống cảnh báo dịch bệnh gia cầm"

    # --- Database ---
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/poultry_disease"
    TEST_DATABASE_URL: str = (
        "postgresql+asyncpg://postgres:postgres@localhost:5432/poultry_disease_test"
    )
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 5
    DATABASE_ECHO: bool = False

    # --- Cảnh báo geospatial ---
    DEFAULT_ALERT_RADIUS_KM: float = 5.0
    RISK_CRITICAL_KM: float = 1.0
    RISK_HIGH_KM: float = 3.0
    RISK_MEDIUM_KM: float = 5.0

    # --- Nguồn dữ liệu ổ dịch (crawler) ---
    # Danh sách URL nguồn dữ liệu, cách nhau bằng dấu phẩy. Để trống thì không nhập gì cả.
    # Định dạng nguồn xem backend/app/services/crawler_service.py. Dữ liệu nhập về luôn ở
    # trạng thái chưa xác nhận và không bao giờ tự động tạo cảnh báo.
    OUTBREAK_FEED_URLS: str = ""
    OUTBREAK_FEED_TIMEOUT: int = 15
    OUTBREAK_FEED_MAX_BYTES: int = 2_000_000
    # Đặt lớn hơn 0 để tự nhập dữ liệu theo chu kỳ (phút). 0 là tắt, chỉ nhập khi cán bộ bấm nút.
    OUTBREAK_CRAWL_INTERVAL_MINUTES: int = 0

    # --- Email (SMTP) ---
    # Đặt EMAIL_ENABLED=true và điền SMTP_* để gửi email cảnh báo tới trang trại có email.
    EMAIL_ENABLED: bool = False
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = ""
    SMTP_FROM_NAME: str = "Cảnh báo dịch gia cầm"
    SMTP_USE_TLS: bool = True  # STARTTLS, thường dùng với cổng 587
    SMTP_USE_SSL: bool = False  # SSL ngay từ đầu, thường dùng với cổng 465
    SMTP_TIMEOUT: int = 10

    # --- JWT ---
    # Không có khóa mặc định. Môi trường production bắt buộc đặt khóa dài tối thiểu 32 ký tự.
    # Môi trường dev để trống thì mỗi lần chạy sinh một khóa ngẫu nhiên, token cũ mất hiệu lực khi khởi động lại.
    JWT_SECRET_KEY: str = ""
    JWT_ALGORITHM: str = "HS256"
    JWT_TOKEN_EXPIRE_MINUTES: int = 60

    # --- Mật khẩu cho tài khoản mẫu khi chạy seed_data ---
    # Để trống thì seed tự sinh mật khẩu ngẫu nhiên và in ra một lần.
    SEED_ADMIN_PASSWORD: str = ""
    SEED_USER_PASSWORD: str = ""

    # --- CORS ---
    BACKEND_CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173"

    @field_validator("BACKEND_CORS_ORIGINS")
    @classmethod
    def _clean_origins(cls, v: str) -> str:
        return ",".join(o.strip() for o in v.split(",") if o.strip())

    @field_validator("OUTBREAK_FEED_URLS")
    @classmethod
    def _check_feed_urls(cls, v: str) -> str:
        urls = [u.strip() for u in v.split(",") if u.strip()]
        for url in urls:
            if urlparse(url).scheme not in ("http", "https"):
                raise ValueError("OUTBREAK_FEED_URLS chỉ chấp nhận địa chỉ http hoặc https")
        return ",".join(urls)

    @model_validator(mode="after")
    def _check_jwt_secret(self) -> "Settings":
        weak = len(self.JWT_SECRET_KEY) < 32
        if self.APP_ENV.lower() == "production":
            if weak:
                raise ValueError(
                    "JWT_SECRET_KEY phải được đặt và dài tối thiểu 32 ký tự khi APP_ENV=production. "
                    "Tạo khóa bằng: python -c \"import secrets; print(secrets.token_urlsafe(48))\""
                )
        elif weak:
            self.JWT_SECRET_KEY = secrets.token_urlsafe(48)
            logging.getLogger("uvicorn.error").warning(
                "JWT_SECRET_KEY chưa đặt hoặc quá ngắn, đang dùng khóa ngẫu nhiên tạm thời cho môi trường dev."
            )
        return self

    @property
    def email_ready(self) -> bool:
        """Đủ cấu hình để gửi email."""
        return self.EMAIL_ENABLED and bool(self.SMTP_HOST) and bool(self.SMTP_FROM or self.SMTP_USER)

    @property
    def outbreak_feed_url_list(self) -> list[str]:
        return [u for u in self.OUTBREAK_FEED_URLS.split(",") if u]

    @property
    def cors_origin_list(self) -> list[str]:
        return [o for o in self.BACKEND_CORS_ORIGINS.split(",") if o]


settings = Settings()
