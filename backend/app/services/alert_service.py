"""Sinh cảnh báo từ ổ dịch."""
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.alert import Alert
from app.models.enums import AlertStatus, OutbreakStatus, RiskLevel
from app.models.outbreak import Outbreak
from app.services.notification_service import Notifier, get_default_notifier
from app.services.risk_service import assess_risk, distance_risk
from app.services.spatial_service import find_farms_within_radius
from app.utils.geo import geometry_to_location


def compute_risk_level(distance_km: float) -> RiskLevel:
    """Mức nguy cơ chỉ theo khoảng cách. Khi tạo cảnh báo dùng assess_risk để xét thêm mức độ ổ dịch."""
    return distance_risk(distance_km)


async def generate_alerts_for_outbreak(
    db: AsyncSession,
    outbreak: Outbreak,
    notifier: Notifier | None = None,
) -> list[Alert]:
    """Tạo cảnh báo mới và đồng bộ mức cho cảnh báo do hệ thống đã tạo.

    Chỉ ổ dịch đang hoạt động và đã được cán bộ xác nhận mới tạo cảnh báo. Ổ dịch nhập từ nguồn
    bên ngoài chưa xác nhận thì không bao giờ phát cảnh báo tới trang trại.
    """
    if outbreak.status != OutbreakStatus.ACTIVE or outbreak.verified is False or outbreak.location is None:
        return []

    notifier = notifier or get_default_notifier()
    loc = geometry_to_location(outbreak.location)
    farms = await find_farms_within_radius(
        db, loc["latitude"], loc["longitude"], outbreak.radius_km
    )

    existing_alerts = list(
        (await db.execute(select(Alert).where(Alert.outbreak_id == outbreak.id))).scalars()
    )
    existing_by_farm = {alert.farm_id: alert for alert in existing_alerts}

    created: list[Alert] = []
    updated: list[Alert] = []
    for farm, distance_km in farms:
        assessment = assess_risk(distance_km, outbreak.severity)
        existing = existing_by_farm.get(farm.id)
        if existing is not None:
            # Cảnh báo do hệ thống tạo có phần căn cứ bắt đầu bằng "Theo khoảng cách".
            # Cập nhật lại mức cho các cảnh báo cũ theo quy tắc mới, nhưng giữ nguyên
            # trạng thái đã gửi/đã xác nhận và không gửi thông báo trùng.
            if existing.risk_basis and existing.risk_basis.startswith("Theo khoảng cách ("):
                new_distance = round(distance_km, 3)
                if (
                    existing.risk_level != assessment.level
                    or existing.risk_basis != assessment.basis
                    or existing.distance_km != new_distance
                ):
                    existing.risk_level = assessment.level
                    existing.risk_basis = assessment.basis
                    existing.distance_km = new_distance
                    updated.append(existing)
            continue

        alert = Alert(
            outbreak_id=outbreak.id,
            farm_id=farm.id,
            distance_km=round(distance_km, 3),
            risk_level=assessment.level,
            risk_basis=assessment.basis,
            message=(
                f"Ổ dịch {outbreak.virus_type} tại {outbreak.province} "
                f"cách trang trại {farm.name} khoảng {distance_km:.2f} km."
            ),
            status=AlertStatus.PENDING,
        )
        db.add(alert)
        created.append(alert)
    await db.flush()

    for alert in created:
        farm = next(f for f, _ in farms if f.id == alert.farm_id)
        try:
            await notifier.send(alert, farm)
            alert.status = AlertStatus.SENT
            alert.sent_at = datetime.now(timezone.utc)
        except Exception:
            alert.status = AlertStatus.FAILED

    await db.commit()
    for alert in [*created, *updated]:
        await db.refresh(alert)
    return [*created, *updated]


__all__ = ["compute_risk_level", "generate_alerts_for_outbreak"]
