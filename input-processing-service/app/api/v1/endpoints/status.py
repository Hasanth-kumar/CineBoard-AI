"""
Processing status endpoints
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
import redis.asyncio as aioredis
import structlog

from app.core.database import get_db
from app.core.redis import get_redis
from app.schemas.input_processing import ProcessingStatusResponse
from app.services.storage_facade import InputStorageService

logger = structlog.get_logger()
router = APIRouter()


@router.get("/status/{input_id}", response_model=ProcessingStatusResponse)
async def get_processing_status(
    input_id: int,
    detailed: bool = False,
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis)
):
    """
    Get processing status for a specific input record
    
    Args:
        input_id: The input record ID
        detailed: If True, returns complete phase data. If False, returns only latest status (default).
    """
    try:
        storage_service = InputStorageService(db, redis)
        
        if detailed:
            status = await storage_service.get_complete_processing_status(input_id)
        else:
            status = await storage_service.get_processing_status(input_id)
        
        if not status:
            raise HTTPException(status_code=404, detail="Input record not found")
        
        logger.info("Processing status retrieved", 
                   input_id=input_id,
                   status=status.status,
                   detailed=detailed)
        
        return status
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get processing status", 
                    input_id=input_id, 
                    error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get status")
