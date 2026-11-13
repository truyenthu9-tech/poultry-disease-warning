"""Dịch vụ thu thập dữ liệu dịch bệnh từ nguồn bên ngoài."""
import time
from urllib.error import URLError

from sqlalchemy.orm import Session

from app.models.outbreak import Disease, OutbreakStatus
from app.models.farm import Farm, FarmStatus

from app.services.spatial_service import nearest_farm


def crawl_disease_data(url: str, db: Session) -> None:
    """Thu thập dữ liệu dịch bệnh từ nguồn bên ngoài."""
    try:
        import requests

        response = requests.get(url, timeout=10)
        response.raise_for_status()
        print(f"[crawler] Đã thu thập dữ liệu từ {url}")
    except (URLError, requests.RequestException) as exc:
        print(f"[crawler] Lỗi khi thu thập dữ liệu từ {url}: {exc}")


def collect_nearby_outbreaks(
    farm: Farm,
    db: Session,
    radius_km: float = 20.0,
) -> list[tuple[Farm, str]]:
    """Thu thập các dịch bệnh gần farm."""
    result: list[tuple[Farm, str]] = []
    for outbreak in db.query(Outbreak).filter(
        Outbreak.status == OutbreakStatus.CONFIRMED
    ).all():
        if outbreak.latitude is None or outbreak.longitude is None:
            continue
        if farm.latitude is None or farm.longitude is None:
            continue
        from app.services.spatial_service import haversine

        distance = haversine(
            farm.latitude, farm.longitude,
            outbreak.latitude, outbreak.longitude,
        )
        if distance <= radius_km:
            result.append((farm, outbreak.disease.value))

    return result


__all__ = ["crawl_disease_data", "collect_nearby_outbreaks"]