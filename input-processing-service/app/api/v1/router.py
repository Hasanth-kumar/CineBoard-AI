"""
API v1 router for Input Processing Service
"""

from fastapi import APIRouter
from app.api.v1.endpoints import health, validation, processing, status

api_router = APIRouter()

# Include endpoint routers
api_router.include_router(
    validation.router,
    prefix="/input",
    tags=["validation"]
)

api_router.include_router(
    processing.router,
    prefix="/input",
    tags=["processing"]
)

api_router.include_router(
    status.router,
    prefix="/input",
    tags=["status"]
)

api_router.include_router(
    health.router,
    prefix="/health",
    tags=["health"]
)

