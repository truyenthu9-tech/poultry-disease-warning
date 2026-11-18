"""Nhập dữ liệu ổ dịch từ nguồn bên ngoài do người vận hành cấu hình.

Hệ thống không gắn sẵn với một website nào. Người vận hành đặt OUTBREAK_FEED_URLS trỏ tới
nguồn dữ liệu mà mình tin cậy và có quyền dùng. Nguồn trả về JSON, là một mảng hoặc
{"items": [...]}, mỗi phần tử có dạng:

    {
      "external_id": "mã bản ghi, duy nhất trong nguồn",
      "virus_type": "H5N1",
      "province": "Hà Nội",
      "district": "Đông Anh",            (tùy chọn)
      "address": "...",                  (tùy chọn)
      "latitude": 21.17,
      "longitude": 105.848,
      "cases_count": 120,                (tùy chọn)
      "reported_date": "2026-11-10T08:00:00+07:00",   (tùy chọn)
      "source_url": "https://...",       (tùy chọn, trang gốc của bản tin)
      "status": "active"                 (tùy chọn: active, contained, closed)
    }

Nguyên tắc an toàn:
- Chưa cấu hình nguồn nào thì không làm gì, chỉ ghi log. Không bao giờ bịa dữ liệu.
- Bản ghi nhập về luôn ở trạng thái CHƯA XÁC NHẬN. Cán bộ thú y phải xác nhận thì hệ thống
  mới cho tạo cảnh báo. Hệ thống không tự gửi cảnh báo từ dữ liệu nhập về.
- Mức độ nghiêm trọng và bán kính cảnh báo lấy giá trị mặc định, cán bộ chỉnh khi xác nhận.
- Nguồn chỉ do cấu hình quyết định, API không nhận địa chỉ từ người dùng.
"""
import json
import logging
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from urllib.parse import urlparse

import httpx
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.enums import OutbreakStatus, Severity
from app.models.outbreak import Outbreak
from app.utils.geo import location_to_geometry

logger = logging.getLogger(__name__)

MAX_ITEMS_PER_FEED = 5000
MAX_ERRORS_REPORTED = 20


class FeedError(Exception):
    """Không đọc được nguồn dữ liệu (lỗi mạng, sai định dạng, vượt giới hạn)."""


class FeedReport(BaseModel):
    """Một bản ghi ổ dịch trong nguồn dữ liệu, đã kiểm tra hợp lệ."""

    model_config = ConfigDict(extra="ignore")

    external_id: str = Field(min_length=1, max_length=255)
    virus_type: str = Field(min_length=1, max_length=255)
    province: str = Field(min_length=1, max_length=100)
    district: str | None = Field(default=None, max_length=100)
    address: str | None = None
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    cases_count: int = Field(default=0, ge=0)
    reported_date: datetime | None = None
    source_url: str | None = Field(default=None, max_length=2000)
    status: OutbreakStatus = OutbreakStatus.ACTIVE

    @field_validator("reported_date")
    @classmethod
    def _assume_utc(cls, v: datetime | None) -> datetime | None:
        # Cột DateTime(timezone=True) cần giờ có múi giờ. Giờ không ghi múi giờ coi là UTC.
        if v is not None and v.tzinfo is None:
            return v.replace(tzinfo=timezone.utc)
        return v

    @field_validator("source_url")
    @classmethod
    def _http_only(cls, v: str | None) -> str | None:
        if v and urlparse(v).scheme not in ("http", "https"):
            raise ValueError("source_url chỉ chấp nhận http hoặc https")
        return v


@dataclass
class CrawlResult:
    sources: int = 0
    reports: list[tuple[str, FeedReport]] = field(default_factory=list)  # (tên nguồn, bản ghi)
    invalid: int = 0
    errors: list[str] = field(default_factory=list)


@dataclass
class ImportSummary:
    sources_configured: int = 0
    fetched: int = 0
    created: int = 0
    duplicates: int = 0
    invalid: int = 0
    errors: list[str] = field(default_factory=list)


def source_name(url: str) -> str:
    """Tên nguồn lưu trong DB và trong log. Chỉ lấy tên máy chủ, tránh lộ token trong URL."""
    return f"feed:{urlparse(url).hostname or 'unknown'}"[:255]


def parse_feed_payload(payload: object) -> tuple[list[FeedReport], int, list[str]]:
    """Kiểm tra dữ liệu JSON của nguồn. Bản ghi sai bị bỏ qua và đếm lại, không làm hỏng cả lô."""
    items = payload.get("items") if isinstance(payload, dict) else payload
    if not isinstance(items, list):
        raise FeedError('Định dạng không hợp lệ: cần một mảng hoặc {"items": [...]}')
    if len(items) > MAX_ITEMS_PER_FEED:
        raise FeedError(f"Nguồn có quá {MAX_ITEMS_PER_FEED} bản ghi")

    reports: list[FeedReport] = []
    invalid = 0
    errors: list[str] = []
    for index, raw in enumerate(items):
        try:
            reports.append(FeedReport.model_validate(raw))
        except ValidationError as exc:
            invalid += 1
            if len(errors) < MAX_ERRORS_REPORTED:
                first = exc.errors()[0]
                where = ".".join(str(p) for p in first["loc"])
                errors.append(f"Bản ghi #{index}: {where}: {first['msg']}")
    return reports, invalid, errors


async def fetch_feed(
    url: str, client: httpx.AsyncClient | None = None
) -> tuple[list[FeedReport], int, list[str]]:
    """Tải và kiểm tra một nguồn. Ném FeedError nếu không dùng được."""
    own_client = client is None
    client = client or httpx.AsyncClient(timeout=settings.OUTBREAK_FEED_TIMEOUT)
    host = source_name(url)
    try:
        chunks: list[bytes] = []
        size = 0
        async with client.stream("GET", url, headers={"Accept": "application/json"}) as response:
            response.raise_for_status()
            async for chunk in response.aiter_bytes():
                size += len(chunk)
                if size > settings.OUTBREAK_FEED_MAX_BYTES:
                    raise FeedError("Dữ liệu vượt quá giới hạn kích thước")
                chunks.append(chunk)
        payload = json.loads(b"".join(chunks))
    except FeedError:
        raise
    except httpx.HTTPError as exc:
        # Không đưa URL đầy đủ vào lỗi vì có thể chứa token
        raise FeedError(f"Không tải được dữ liệu ({type(exc).__name__})") from exc
    except ValueError as exc:
        raise FeedError("Dữ liệu không phải JSON hợp lệ") from exc
    finally:
        if own_client:
            await client.aclose()
    logger.info("Đã tải nguồn %s", host)
    return parse_feed_payload(payload)


async def collect_reports(client: httpx.AsyncClient | None = None) -> CrawlResult:
    """Tải mọi nguồn đã cấu hình. Một nguồn lỗi không chặn các nguồn còn lại."""
    urls = settings.outbreak_feed_url_list
    result = CrawlResult(sources=len(urls))
    if not urls:
        logger.info("Chưa cấu hình OUTBREAK_FEED_URLS, không có nguồn dữ liệu ổ dịch để nhập.")
        return result

    for url in urls:
        name = source_name(url)
        try:
            reports, invalid, errors = await fetch_feed(url, client=client)
        except FeedError as exc:
            logger.warning("Nguồn %s lỗi: %s", name, exc)
            result.errors.append(f"{name}: {exc}")
            continue
        result.reports.extend((name, r) for r in reports)
        result.invalid += invalid
        result.errors.extend(f"{name}: {e}" for e in errors)
    result.errors = result.errors[:MAX_ERRORS_REPORTED]
    return result


async def crawl_outbreaks(client: httpx.AsyncClient | None = None) -> list[dict]:
    """Trả về các bản ghi hợp lệ từ mọi nguồn đã cấu hình. Chưa cấu hình nguồn thì trả về danh sách rỗng."""
    result = await collect_reports(client)
    return [{"source": name, **r.model_dump(mode="json")} for name, r in result.reports]


async def import_reports(db: AsyncSession, reports: list[tuple[str, FeedReport]]) -> ImportSummary:
    """Lưu bản ghi mới thành ổ dịch CHƯA XÁC NHẬN. Bản ghi đã có (cùng nguồn và external_id) bị bỏ qua."""
    summary = ImportSummary(fetched=len(reports))

    existing: set[tuple[str, str | None]] = set()
    sources = {name for name, _ in reports}
    if sources:
        rows = await db.execute(
            select(Outbreak.source, Outbreak.external_id).where(Outbreak.source.in_(list(sources)))
        )
        existing = {(s, e) for s, e in rows.all()}

    for name, report in reports:
        key = (name, report.external_id)
        if key in existing:
            summary.duplicates += 1
            continue
        existing.add(key)
        outbreak = Outbreak(
            virus_type=report.virus_type,
            province=report.province,
            district=report.district,
            address=report.address,
            location=location_to_geometry(report.latitude, report.longitude),
            cases_count=report.cases_count,
            status=report.status,
            severity=Severity.MEDIUM,
            radius_km=settings.DEFAULT_ALERT_RADIUS_KM,
            source=name,
            source_url=report.source_url,
            external_id=report.external_id,
            verified=False,
        )
        if report.reported_date is not None:
            outbreak.reported_date = report.reported_date
        db.add(outbreak)
        summary.created += 1

    try:
        await db.commit()
    except IntegrityError:
        # Hai lần nhập chạy đồng thời cùng lưu một bản ghi
        await db.rollback()
        summary.created = 0
        summary.errors.append("Xung đột khi lưu, có thể một lần nhập khác đang chạy. Hãy thử lại.")
    return summary


async def run_import(db: AsyncSession, client: httpx.AsyncClient | None = None) -> dict:
    """Tải mọi nguồn rồi lưu bản ghi mới. Trả về số liệu tổng hợp để hiển thị cho cán bộ."""
    crawled = await collect_reports(client)
    summary = await import_reports(db, crawled.reports)
    summary.sources_configured = crawled.sources
    summary.invalid = crawled.invalid
    summary.errors = (crawled.errors + summary.errors)[:MAX_ERRORS_REPORTED]
    return asdict(summary)


__all__ = [
    "FeedError", "FeedReport", "CrawlResult", "ImportSummary", "source_name", "parse_feed_payload",
    "fetch_feed", "collect_reports", "crawl_outbreaks", "import_reports", "run_import",
]
