"""Router API quản lý cảnh báo."""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.api.schemas.alert import AlertCreate, AlertResponse, AlertUpdate
from app.models.alert import Alert, AlertStatusEnum, RiskLevelEnum
from app.models.outbreak import Outbreak
from app.services.spatial_service import find_farms_within_radius

from .deps import get_current_user

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("", response_model=list[AlertResponse])
def list_alerts(
    risk_level: str | None = Query(default=None, pattern=r"^(low|medium|high|very_high)$"),
    status: str | None = Query(default=None),
    farm_id: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db),
) -> list[AlertResponse]:
    """Danh sách cảnh báo."""

    statement = db.query(Alert)
    if risk_level is not None:
        statement = statement.filter(func.lower(Alert.risk_level) == func.lower(risk_level))
    if status is not None:
        statement = statement.filter(func.lower(Alert.status) == func.lower(status))
    if farm_id is not None:
        statement = statement.filter(Alert.farm_id == farm_id)

    results = statement.order_by(Alert.created_at.desc()).offset((page - 1) * size).limit(size).all()
    return [AlertResponse.model_validate(a) for a in results]


@router.get("/{alert_id}", response_model=AlertResponse)
def get_alert(
    alert_id: str,
    db: Session = Depends(get_db),
) -> AlertResponse:
    """Lấy thông tin một cảnh báo."""
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if alert is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy cảnh báo")
    return AlertResponse.model_validate(alert)


@router.post("", response_model=AlertResponse, status_code=status.HTTP_201_CREATED)
def create_alert(
    payload: AlertCreate,
    db: Session = Depends(get_db),
) -> AlertResponse:
    """Tạo một cảnh báo mới với tính toán khoảng cách."""
    # Validate outbreak exists and get its location
    outbreak = db.query(Outbreak).filter(Outbreak.id == payload.outbreak_id).first()
    if not outbreak:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy ổ dịch")

    # If farm_id is provided and outbreak has location, compute distance
    alert = Alert(
        id=None,  # Will be auto-generated
        outbreak_id=payload.outbreak_id,
        farm_id=payload.farm_id,
        risk_level=payload.risk_level,
        message=payload.message,
    )

    db.add(alert)
    db.commit()
    db.refresh(alert)

    # Compute distance if both outbreak and farm have locations
    if alert.farm_id is not None:
        try:
            # Query the farm to get its location WKT
            farm = db.query(Outbreak).filter(Outbreak.id == payload.outbreak_id).first()
            if farm and farm.location:
                outbreak_wkt = str(farm.location)  # GeoAlchemy2 stores as string already

                # For alert's distance calculation, we need outbreak location vs farm location
                # Since we just created the alert with a farm_id, we should get that farm
                from app.models.farm import Farm
                alert_farm = db.query(Farm).filter(Farm.id == alert.farm_id).first()
                
                if alert_farm and alert_farm.location:
                    # Query directly for distance using ST_Distance between outbreak location and farm location
                    distance_expr = func.ST_Distance(outbreak.location, alert_farm.location) / 1000.0
                    result = db.session.execute(distance_expr).scalar()
                    alert.distance_km = float(result) if result else 0.0
        except Exception:
            # If spatial functions fail, default to 0.0
            alert.distance_km = 0.0

    return AlertResponse.model_validate(alert)


@router.put("/{alert_id}", response_model=AlertResponse)
def update_alert(
    alert_id: str,
    payload: AlertUpdate,
    db: Session = Depends(get_db),
) -> AlertResponse:
    """Cập nhật cảnh báo."""
    alert = db.get(Alert, alert_id)
    if alert is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy cảnh báo")

    if payload.risk_level is not None:
        alert.risk_level = payload.risk_level

    if payload.message is not None:
        alert.message = payload.message

    if payload.status is not None:
        alert.status = payload.status

    db.commit()
    db.refresh(alert)
    return AlertResponse.model_validate(alert)


@router.delete("/{alert_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_alert(
    alert_id: str,
    db: Session = Depends(get_db),
) -> None:
    """Xóa cảnh báo."""
    alert = db.get(Alert, alert_id)
    if alert is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy cảnh báo")
    db.delete(alert)
    db.commit()


__all__ = ["router"]
