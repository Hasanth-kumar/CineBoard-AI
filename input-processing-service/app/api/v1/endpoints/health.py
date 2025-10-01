"""
Health check endpoints for Input Processing Service
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import structlog

from app.core.database import get_db
from app.core.redis import get_redis
from app.core.config import settings

logger = structlog.get_logger()
router = APIRouter()


@router.get("/")
async def health_check():
    """Basic health check endpoint"""
    return {
        "status": "healthy",
        "service": "input-processing-service",
        "version": settings.SERVICE_VERSION
    }


@router.get("/detailed")
async def detailed_health_check(
    db: AsyncSession = Depends(get_db),
    redis = Depends(get_redis)
):
    """Detailed health check with database and Redis connectivity"""
    
    health_status = {
        "status": "healthy",
        "service": "input-processing-service",
        "version": settings.SERVICE_VERSION,
        "checks": {}
    }
    
    # Check database connectivity
    try:
        await db.execute(text("SELECT 1"))
        health_status["checks"]["database"] = {
            "status": "healthy",
            "message": "Database connection successful"
        }
    except Exception as e:
        logger.error("Database health check failed", error=str(e))
        health_status["checks"]["database"] = {
            "status": "unhealthy",
            "message": f"Database connection failed: {str(e)}"
        }
        health_status["status"] = "unhealthy"
    
    # Check Redis connectivity
    try:
        await redis.ping()
        health_status["checks"]["redis"] = {
            "status": "healthy",
            "message": "Redis connection successful"
        }
    except Exception as e:
        logger.error("Redis health check failed", error=str(e))
        health_status["checks"]["redis"] = {
            "status": "unhealthy",
            "message": f"Redis connection failed: {str(e)}"
        }
        health_status["status"] = "unhealthy"
    
    # Return appropriate status code
    if health_status["status"] == "unhealthy":
        raise HTTPException(status_code=503, detail=health_status)
    
    return health_status


@router.get("/ready")
async def readiness_check(
    db: AsyncSession = Depends(get_db),
    redis = Depends(get_redis)
):
    """Readiness check for Kubernetes"""
    
    # Check if all dependencies are ready
    try:
        # Check database
        await db.execute(text("SELECT 1"))
        
        # Check Redis
        await redis.ping()
        
        return {"status": "ready"}
        
    except Exception as e:
        logger.error("Readiness check failed", error=str(e))
        raise HTTPException(status_code=503, detail="Service not ready")

