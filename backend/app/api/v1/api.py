"""Router tổng hợp các endpoint API v1."""
from fastapi import APIRouter

from .endpoints.farms import farm_router
from .endpoints.outbreaks import outbreak_router
from .endpoints.alerts import alert_router
from .endpoints.auth import auth_router
from .endpoints.geo_farms import geo_farms_router

router = APIRouter(prefix="/api/v1", tags=["api"])

router.include_router(auth_router, prefix="/auth", tags=["auth"])
router.include_router(farm_router, tags=["farms"])
router.include_router(outbreak_router, tags=["outbreaks"])
router.include_router(alert_router, tags=["alerts"])
router.include_router(geo_farms_router, prefix="/geo", tags=["spatial"])


__all__ = ["router"]
