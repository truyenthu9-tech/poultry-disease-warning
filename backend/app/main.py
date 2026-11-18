"""Điểm vào của ứng dụng FastAPI."""
import asyncio
import contextlib
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from sqlalchemy import text
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.api import router
from app.core.config import settings
from app.core.database import async_session_maker, close_db
from app.db.init_db import init_db

logger = logging.getLogger("uvicorn.error")


async def _crawl_loop(interval_minutes: int) -> None:
    """Nhập ổ dịch từ nguồn dữ liệu theo chu kỳ. Chỉ nhập, không bao giờ tự tạo cảnh báo."""
    from app.services.crawler_service import run_import

    while True:
        try:
            async with async_session_maker() as session:
                summary = await run_import(session)
            logger.info("Nhập dữ liệu ổ dịch tự động: %s", summary)
        except Exception:
            logger.exception("Nhập dữ liệu ổ dịch tự động bị lỗi")
        await asyncio.sleep(interval_minutes * 60)


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        await init_db()
    except Exception as exc:  # DB chưa sẵn sàng thì vẫn cho server chạy để xem /docs
        logger.warning("Không kết nối được database lúc khởi động: %s", exc)
    crawl_task = None
    if settings.OUTBREAK_CRAWL_INTERVAL_MINUTES > 0 and settings.outbreak_feed_url_list:
        crawl_task = asyncio.create_task(_crawl_loop(settings.OUTBREAK_CRAWL_INTERVAL_MINUTES))
    yield
    if crawl_task is not None:
        crawl_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await crawl_task
    await close_db()


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=settings.DESCRIPTION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix=settings.API_V1_STR)


@app.get("/health", tags=["Health"])
async def health_check() -> JSONResponse:
    """Kiểm tra thật sự kết nối database. Trả 503 khi database không dùng được."""
    info = {"service": settings.PROJECT_NAME, "version": settings.VERSION}
    try:
        async with async_session_maker() as session:
            await session.execute(text("SELECT 1"))
    except Exception:
        logger.warning("Health check: không kết nối được database", exc_info=False)
        return JSONResponse(status_code=503, content={"status": "unhealthy", "database": "down", **info})
    return JSONResponse(content={"status": "healthy", "database": "up", **info})


@app.get("/", tags=["Root"])
async def root() -> dict:
    return {
        "name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "description": settings.DESCRIPTION,
        "docs_url": f"{settings.API_V1_STR}/docs",
        "redoc_url": f"{settings.API_V1_STR}/redoc",
    }
