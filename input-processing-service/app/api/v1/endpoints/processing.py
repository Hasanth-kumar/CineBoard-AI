"""
Input processing endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
import redis.asyncio as aioredis
import structlog

from app.core.database import get_db
from app.core.redis import get_redis
from app.schemas.input_processing import (
    InputProcessingRequest,
    InputProcessingResponse
)
from app.services.storage_facade import InputStorageService
from app.workflows.pipeline import process_input_pipeline

logger = structlog.get_logger()
router = APIRouter()


@router.post("/process", response_model=InputProcessingResponse)
async def process_input(
    request: InputProcessingRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis)
):
    """
    Complete input processing pipeline: validation, language detection, translation, preprocessing
    """
    try:
        logger.info("Input processing request", input_length=len(request.text))
        
        # Initialize storage service
        storage_service = InputStorageService(db, redis)
        
        # Start processing pipeline
        input_record = await storage_service.create_input_record(
            user_id=request.user_id,
            raw_input=request.text,
            session_id=request.session_id
        )
        
        # Create response object
        response = InputProcessingResponse(
            input_id=input_record.id,
            status="pending",
            message="Input processing started successfully"
        )
        
        # Add background processing task
        # Note: Background tasks need their own database session since the request session closes
        background_tasks.add_task(
            process_input_pipeline,
            input_record.id,
            request.text,
            request.user_id
        )
        
        logger.info("Input processing started", 
                   input_id=input_record.id,
                   status=response.status)
        
        return response
        
    except Exception as e:
        logger.error("Input processing failed", error=str(e))
        raise HTTPException(status_code=500, detail="Processing failed")
