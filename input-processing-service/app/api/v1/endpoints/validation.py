"""
Input validation endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from app.core.database import get_db
from app.core.redis import get_redis
from app.schemas.input_processing import (
    InputValidationRequest,
    InputValidationResponse
)
from app.services.input_validation import InputValidationService

logger = structlog.get_logger()
router = APIRouter()


@router.post("/validate", response_model=InputValidationResponse)
async def validate_input(
    request: InputValidationRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    redis = Depends(get_redis)
):
    """
    Validate input text for content policy, length, and format
    """
    try:
        logger.info("Input validation request", input_length=len(request.text))
        
        # Initialize validation service
        validation_service = InputValidationService(db, redis)
        
        # Perform validation
        validation_result = await validation_service.validate_input(
            text=request.text,
            user_id=request.user_id,
            session_id=request.session_id
        )
        
        logger.info("Input validation completed", 
                   status=validation_result.status,
                   validation_id=validation_result.validation_id)
        
        return validation_result
        
    except Exception as e:
        logger.error("Input validation failed", error=str(e))
        raise HTTPException(status_code=500, detail="Validation failed")
