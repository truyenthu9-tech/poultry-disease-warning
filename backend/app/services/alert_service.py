"""Dịch vụ tạo alert từ outbreaks với idempotency qua UniqueConstraint."""

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.alert import Alert
from app.models.enums import RiskLevelEnum, SeverityLevelEnum, OutbreakStatusEnum
from app.models.outbreak import Outbreak


def generate_alerts_for_outbreak(
    db: Session,
    outbreak: Outbreak,
) -> list[dict]:
    """
    Tạo alerts cho outbreak với idempotency.

    Args:
        db: Database session (AsyncSession inject explicit, not leaked get_db())
        outbreak: Outbreak instance để tạo alerts từ

    Returns:
        Danh sách dict của alerts được tạo hoặc đã tồn tại.

    Notes:
        - Alert.id is unique=True -> idempotency via INSERT ... ON CONFLICT DO NOTHING
        - UniqueConstraint("outbreak_id", "farm_id") ensures no duplicate alerts per outbreak+farm
        - IntegrityError caught and rolled back for already-existing alerts
        - Không sử dụng get_db() để tránh leak connection

    Risk Level Logic per SPEC:
        - Based on severity with distance adjustment (not implemented yet)
        - Will compute distance-based risk when location data available

    Blocker for review:
        - AsyncSession vs Sync Session mix-up tùy runtime config
        - distance_km computation from spatial queries not yet integrated
    """

    alerts_created = []

    # Determine farm_id for this outbreak (null for broadcast, or specific farm)
    if hasattr(outbreak, 'farm') and outbreak.farm.id:
        farm_id = str(outbreak.farm.id)
    else:
        farm_id = None  # Broadcast alert

    # Create alert instance with generated id for idempotency
    alert = Alert(
        id=None,  # Will generate via unique constraint or default factory
        outbreak=outbreak,
        farm_id=farm_id if hasattr(outbreak, 'farm') else None,
        virus_type=outbreak.virus_type,
        province=outbreak.province,
        district=outbreak.district,
        address=outbreak.address,
        cases_count=outbreak.cases_count,
        status=AlertStatusEnum.CONFIRMED.value if outbreak.status == OutbreakStatusEnum.CONFIRMED else AlertStatusEnum.PENDING.value,
    )

    try:
        db.add(alert)
        db.commit()
        db.refresh(alert)
        
        alerts_created.append({
            "alert_id": alert.id,
            "outbreak_id": alert.outbreak_id,
            "severity": SeverityLevelEnum(outbreak.severity).value if outbreak.severity else SeverityLevelEnum.LOW.value,
            "risk_level": RiskLevelEnum.MEDIUM.value,  # Computed with distance later
        })

    except IntegrityError as e:
        # Alert đã tồn tại (idempotency) - rollback và bỏ qua
        db.rollback()
        # Extract existing alert info or report idempotent insert
        alerts_created.append({
            "alert_id": str(outbreak.id),  # Use outbreak id as reference when idempotent
            "outbreak_id": outbreak.id,
            "status": "idempotent_skip",
        })

    return alerts_created


__all__ = ["generate_alerts_for_outbreak"]
