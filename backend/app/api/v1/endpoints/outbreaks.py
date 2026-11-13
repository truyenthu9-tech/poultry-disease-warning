"""Router API quản lý dịch bệnh."""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.outbreak import Outbreak
from app.schemas.outbreak import OutbreakCreate, OutbreakResponse, OutbreakUpdate
from app.services.alert_service import notify_outbreak
from app.api.deps import get_current_user

from .deps import get_current_user

router = APIRouter(prefix="/outbreaks", tags=["outbreaks"])


@router.get("", response_model=list[OutbreakResponse])
def list_outbreaks(
    page: int = Query(default=1, ge=1),
    size: int = Query(default=10, ge=1, le=100),
    disease: Disease | None = Query(default=None),
    status: OutbreakStatus | None = Query(default=None),
    db: Session = Depends(get_db),
) -> list[OutbreakResponse]:
    """Danh sách dịch bệnh."""

    statement = db.query(Outbreak)
    if disease is not None:
        statement = statement.filter(Outbreak.disease == disease)
    if status is not None:
        statement = statement.filter(Outbreak.status == status)

    results = statement.order_by(Outbreak.detected_at.desc()).offset((page - 1) * size).limit(size).all()
    return [OutbreakResponse.model_validate(o) for o in results]


@router.get("/{outbreak_id}", response_model=OutbreakResponse)
def get_outbreak(
    outbreak_id: str,
    db: Session = Depends(get_db),
) -> OutbreakResponse:
    """Lấy thông tin một dịch bệnh."""
    outbreak = db.get(Outbreak, outbreak_id)
    if outbreak is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy dịch bệnh")
    return OutbreakResponse.model_validate(outbreak)


@router.post("", response_model=OutbreakResponse, status_code=status.HTTP_201_CREATED)
def create_outbreak(
    payload: OutbreakCreate,
    db: Session = Depends(get_db),
) -> OutbreakResponse:
    """Báo cáo một dịch bệnh mới."""
    from app.models.farm import Farm

    farm = db.get(Farm, payload.farm_id)
    if farm is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy trang trại")

    outbreak = Outbreak(
        disease=payload.disease,
        symptom=payload.symptom,
        detected_at=payload.detected_at or datetime.now(timezone.utc),
        description=payload.description,
        farm=farm,
    )
    db.add(outbreak)
    db.commit()
    db.refresh(outbreak)

    # Thông báo cho các trang trại lân cận.
    notify_outbreak(outbreak)

    return OutbreakResponse.model_validate(outbreak)


@router.put("/{outbreak_id}", response_model=OutbreakResponse)
def update_outbreak(
    outbreak_id: str,
    payload: OutbreakUpdate,
    db: Session = Depends(get_db),
) -> OutbreakResponse:
    """Cập nhật thông tin dịch bệnh."""
    outbreak = db.get(Outbreak, outbreak_id)
    if outbreak is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy dịch bệnh")

    if payload.disease is not None:
        outbreak.disease = payload.disease

    if payload.symptom is not None:
        outbreak.symptom = payload.symptom

    if payload.status is not None:
        outbreak.status = payload.status

    if payload.description is not None:
        outbreak.description = payload.description

    db.commit()
    db.refresh(outbreak)
    return OutbreakResponse.model_validate(outbreak)


@router.delete("/{outbreak_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_outbreak(
    outbreak_id: str,
    db: Session = Depends(get_db),
) -> None:
    """Xóa dịch bệnh."""
    outbreak = db.get(Outbreak, outbreak_id)
    if outbreak is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy dịch bệnh")
    db.delete(outbreak)
    db.commit()


__all__ = ["router"]