"""Gộp router API v1 (prefix /api/v1 được thêm ở main.py)."""
from fastapi import APIRouter, Depends

from app.api.deps import get_current_user

from app.api.v1.endpoints.alerts import alert_router
from app.api.v1.endpoints.auth import auth_router
from app.api.v1.endpoints.farms import farm_router
from app.api.v1.endpoints.farm_registrations import farm_registration_router
from app.api.v1.endpoints.geo_farms import geo_farms_router
from app.api.v1.endpoints.outbreaks import outbreak_router
from app.api.v1.endpoints.outbreak_reports import outbreak_report_router

router = APIRouter()
router.include_router(auth_router, prefix="/auth", tags=["auth"])
# Mọi route nghiệp vụ đều yêu cầu đăng nhập. Thao tác ghi cần thêm quyền ở từng endpoint.
_auth = [Depends(get_current_user)]
router.include_router(farm_router, tags=["farms"], dependencies=_auth)
router.include_router(farm_registration_router, tags=["farm-registrations"], dependencies=_auth)
router.include_router(outbreak_router, tags=["outbreaks"], dependencies=_auth)
router.include_router(outbreak_report_router, tags=["outbreak-reports"], dependencies=_auth)
router.include_router(alert_router, tags=["alerts"], dependencies=_auth)
router.include_router(geo_farms_router, prefix="/geo", tags=["spatial"], dependencies=_auth)

__all__ = ["router"]
