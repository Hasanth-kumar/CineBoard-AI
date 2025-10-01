"""
API v1 router for Input Processing Service
"""

from fastapi import APIRouter
from app.api.v1.endpoints import input_processing, health

api_router = APIRouter()

# Include endpoint routers
api_router.include_router(
    input_processing.router,
    prefix="/input",
    tags=["input-processing"]
)

api_router.include_router(
    health.router,
    prefix="/health",
    tags=["health"]
)

