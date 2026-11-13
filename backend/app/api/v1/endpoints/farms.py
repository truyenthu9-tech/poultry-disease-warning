"""Router API quản lý trang trại chăn nuôi."""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.api.schemas.farm import FarmCreate, FarmResponse, FarmUpdate
from app.core.database import get_db
from app.models.farm import Farm, FarmStatus, FarmType
from app.services.alert_service import notify_outbreak

from .deps import get_current_user

router = APIRouter(prefix="/farms", tags=["farms"])


@router.get("", response_model=list[FarmResponse])
def list_farms(
    status: FarmStatus | None = Query(default=None),
    farm_type: FarmType | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=10, ge=1, le=100),
    q: str = Query(default="", max_length=255),
    db: Session = Depends(get_db),
) -> list[FarmResponse]:
    """Danh sách trang trại."""

    statement = db.query(Farm)
    if status is not None:
        statement = statement.filter(Farm.status == status)
    if farm_type is not None:
        statement = statement.filter(Farm.farm_type == farm_type)
    if q:
        statement = statement.filter(
            (Farm.owner_name.ilike(f"%{q}%"))
            | (Farm.province.ilike(f"%{q}%"))
            | (Farm.address.ilike(f"%{q}%"))
        )

    results = statement.order_by(Farm.created_at.desc()).offset((page - 1) * size).limit(size).all()
    return [FarmResponse.model_validate(f) for f in results]


@router.get("/{farm_id}", response_model=FarmResponse)
def get_farm(
    farm_id: str,
    db: Session = Depends(get_db),
) -> FarmResponse:
    """Lấy thông tin một trang trại."""
    farm = db.get(Farm, farm_id)
    if farm is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy trang trại")
    return FarmResponse.model_validate(farm)


@router.post("", response_model=FarmResponse, status_code=status.HTTP_201_CREATED)
def create_farm(
    payload: FarmCreate,
    db: Session = Depends(get_db),
) -> FarmResponse:
    """Tạo một trang trại mới."""
    from app.models.farm import Farm

    farm = Farm(
        owner_name=payload.owner_name,
        address=payload.address,
        province=payload.province,
        district=payload.district,
        latitude=payload.latitude,
        longitude=payload.longitude,
        farm_type=payload.farm_type,
        phone=payload.phone,
        notes=payload.notes,
    )
    db.add(farm)
    db.commit()
    db.refresh(farm)
    return FarmResponse.model_validate(farm)


@router.put("/{farm_id}", response_model=FarmResponse)
def update_farm(
    farm_id: str,
    payload: FarmUpdate,
    db: Session = Depends(get_db),
) -> FarmResponse:
    """Cập nhật thông tin trang trại."""
    farm = db.get(Farm, farm_id)
    if farm is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy trang trại")

    if payload.owner_name is not None:
        if not payload.owner_name or len(payload.owner_name) < 2:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Tên không hợp lệ")
        farm.owner_name = payload.owner_name

    if payload.address is not None:
        farm.address = payload.address

    if payload.province is not None:
        farm.province = payload.province

    if payload.district is not None:
        farm.district = payload.district

    if payload.latitude is not None:
        farm.latitude = payload.latitude

    if payload.longitude is not None:
        farm.longitude = payload.longitude

    if payload.farm_type is not None:
        farm.farm_type = payload.farm_type

    if payload.phone is not None:
        farm.phone = payload.phone

    if payload.notes is not None:
        farm.notes = payload.notes

    db.commit()
    db.refresh(farm)
    return FarmResponse.model_validate(farm)


@router.delete("/{farm_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_farm(
    farm_id: str,
    db: Session = Depends(get_db),
) -> None:
    """Xóa trang trại."""
    farm = db.get(Farm, farm_id)
    if farm is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy trang trại")
    db.delete(farm)
    db.commit()


__all__ = ["router"]