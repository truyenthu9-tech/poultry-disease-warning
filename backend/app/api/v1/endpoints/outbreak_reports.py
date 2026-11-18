"""Người dùng gửi báo cáo riêng; cán bộ xác nhận mới tạo ổ dịch công khai."""
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_staff
from app.core.config import settings
from app.core.database import get_db
from app.models.enums import OutbreakStatus, Severity
from app.models.outbreak import Outbreak
from app.models.outbreak_report import OutbreakReport
from app.schemas.outbreak_report import OutbreakReportCreate, OutbreakReportReject, OutbreakReportResponse
from app.schemas.user import UserResponse
from app.utils.geo import location_to_geometry

outbreak_report_router = APIRouter(prefix="/outbreak-reports")


async def _pending_report(db: AsyncSession, report_id: uuid.UUID) -> OutbreakReport:
    report = await db.scalar(
        select(OutbreakReport).where(OutbreakReport.id == report_id).with_for_update()
    )
    if report is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy báo cáo dịch bệnh")
    if report.status != "pending":
        raise HTTPException(status.HTTP_409_CONFLICT, "Báo cáo này đã được xử lý")
    return report


@outbreak_report_router.post("", response_model=OutbreakReportResponse, status_code=status.HTTP_201_CREATED)
async def submit_outbreak_report(
    payload: OutbreakReportCreate,
    db: AsyncSession = Depends(get_db),
    current: UserResponse = Depends(get_current_user),
):
    data = payload.model_dump(exclude={"location"})
    report = OutbreakReport(
        **data,
        submitted_by_id=current.id,
        location=location_to_geometry(payload.location.latitude, payload.location.longitude),
        status="pending",
    )
    db.add(report)
    await db.commit()
    await db.refresh(report)
    return report


@outbreak_report_router.get("/mine", response_model=list[OutbreakReportResponse])
async def list_my_outbreak_reports(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current: UserResponse = Depends(get_current_user),
):
    stmt = (
        select(OutbreakReport)
        .where(OutbreakReport.submitted_by_id == current.id)
        .order_by(OutbreakReport.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    return list((await db.execute(stmt)).scalars())


@outbreak_report_router.get("", response_model=list[OutbreakReportResponse], dependencies=[Depends(require_staff)])
async def list_outbreak_reports(
    status_: str | None = Query(default="pending", alias="status", pattern="^(pending|approved|rejected)$"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(OutbreakReport)
    if status_ is not None:
        stmt = stmt.where(OutbreakReport.status == status_)
    stmt = stmt.order_by(OutbreakReport.created_at.asc()).offset((page - 1) * page_size).limit(page_size)
    return list((await db.execute(stmt)).scalars())


@outbreak_report_router.post("/{report_id}/approve", response_model=OutbreakReportResponse)
async def approve_outbreak_report(
    report_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current: UserResponse = Depends(require_staff),
):
    report = await _pending_report(db, report_id)
    now = datetime.now(timezone.utc)
    outbreak = Outbreak(
        virus_type=report.virus_type,
        province=report.province,
        district=report.district,
        commune=report.commune,
        hamlet=report.hamlet,
        address=report.address,
        location=report.location,
        cases_count=report.cases_count,
        status=OutbreakStatus.ACTIVE,
        severity=Severity.MEDIUM,
        radius_km=settings.DEFAULT_ALERT_RADIUS_KM,
        onset_date=report.onset_date,
        source="user_report",
        external_id=str(report.id),
        verified=True,
        verified_at=now,
        verified_by_id=current.id,
    )
    db.add(outbreak)
    await db.flush()
    report.status = "approved"
    report.reviewed_by_id = current.id
    report.reviewed_at = now
    report.outbreak_id = outbreak.id
    await db.commit()
    await db.refresh(report)
    return report


@outbreak_report_router.post("/{report_id}/reject", response_model=OutbreakReportResponse)
async def reject_outbreak_report(
    report_id: uuid.UUID,
    payload: OutbreakReportReject,
    db: AsyncSession = Depends(get_db),
    current: UserResponse = Depends(require_staff),
):
    report = await _pending_report(db, report_id)
    report.status = "rejected"
    report.reviewed_by_id = current.id
    report.reviewed_at = datetime.now(timezone.utc)
    report.review_note = payload.review_note
    await db.commit()
    await db.refresh(report)
    return report


__all__ = ["outbreak_report_router"]
