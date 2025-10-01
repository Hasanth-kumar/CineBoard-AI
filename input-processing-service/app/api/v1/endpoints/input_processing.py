"""
Input processing endpoints for Input Processing Service
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import structlog

from app.core.database import get_db
from app.core.redis import get_redis
from app.core.config import settings
from app.schemas.input_processing import (
    InputValidationRequest,
    InputValidationResponse,
    InputProcessingRequest,
    InputProcessingResponse,
    ProcessingStatusResponse
)
from app.services.input_validation import InputValidationService
from app.services.language_detection import LanguageDetectionService
from app.services.translation import TranslationService
from app.services.text_preprocessing import TextPreprocessingService
from app.services.input_storage import InputStorageService

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


@router.post("/process", response_model=InputProcessingResponse)
async def process_input(
    request: InputProcessingRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    redis = Depends(get_redis)
):
    """
    Complete input processing pipeline: validation, language detection, translation, preprocessing
    """
    try:
        logger.info("Input processing request", input_length=len(request.text))
        
        # Initialize services
        validation_service = InputValidationService(db, redis)
        language_service = LanguageDetectionService(db, redis)
        translation_service = TranslationService(db, redis)
        preprocessing_service = TextPreprocessingService(db, redis)
        storage_service = InputStorageService(db, redis)
        
        # Start processing pipeline
        processing_result = await storage_service.create_input_record(
            user_id=request.user_id,
            raw_input=request.text,
            session_id=request.session_id
        )
        
        # Add background processing task
        background_tasks.add_task(
            process_input_pipeline,
            processing_result.input_id,
            request.text,
            request.user_id,
            db,
            redis
        )
        
        logger.info("Input processing started", 
                   input_id=processing_result.input_id,
                   status=processing_result.status)
        
        return processing_result
        
    except Exception as e:
        logger.error("Input processing failed", error=str(e))
        raise HTTPException(status_code=500, detail="Processing failed")


@router.get("/status/{input_id}", response_model=ProcessingStatusResponse)
async def get_processing_status(
    input_id: int,
    db: AsyncSession = Depends(get_db),
    redis = Depends(get_redis)
):
    """
    Get processing status for a specific input record
    """
    try:
        storage_service = InputStorageService(db, redis)
        
        status = await storage_service.get_processing_status(input_id)
        
        if not status:
            raise HTTPException(status_code=404, detail="Input record not found")
        
        logger.info("Processing status retrieved", 
                   input_id=input_id,
                   status=status.status)
        
        return status
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get processing status", 
                    input_id=input_id, 
                    error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get status")


async def process_input_pipeline(
    input_id: int,
    text: str,
    user_id: int,
    db: AsyncSession,
    redis
):
    """
    Background task for processing input through the complete pipeline
    """
    try:
        logger.info("Starting input processing pipeline", input_id=input_id)
        
        # Initialize services
        validation_service = InputValidationService(db, redis)
        language_service = LanguageDetectionService(db, redis)
        translation_service = TranslationService(db, redis)
        preprocessing_service = TextPreprocessingService(db, redis)
        storage_service = InputStorageService(db, redis)
        
        # Phase 1: Validation
        await storage_service.update_processing_status(
            input_id, "validation", "processing", 10
        )
        
        validation_result = await validation_service.validate_input(
            text=text, user_id=user_id
        )
        
        if validation_result.status != "valid":
            await storage_service.update_processing_status(
                input_id, "validation", "failed", 0,
                error_message="Validation failed",
                error_details={"validation_result": validation_result.dict()}
            )
            return
        
        await storage_service.update_processing_status(
            input_id, "validation", "completed", 25
        )
        
        # Phase 2: Language Detection
        await storage_service.update_processing_status(
            input_id, "language_detection", "processing", 30
        )
        
        language_result = await language_service.detect_language(text)
        
        await storage_service.update_processing_status(
            input_id, "language_detection", "completed", 50,
            phase_data={"language_result": language_result.dict()}
        )
        
        # Phase 3: Translation (if needed)
        processed_text = text
        if language_result.language != "en":
            await storage_service.update_processing_status(
                input_id, "translation", "processing", 60
            )
            
            translation_result = await translation_service.translate_text(
                text, language_result.language, "en"
            )
            
            processed_text = translation_result.translated_text
            
            await storage_service.update_processing_status(
                input_id, "translation", "completed", 75,
                phase_data={"translation_result": translation_result.dict()}
            )
        else:
            await storage_service.update_processing_status(
                input_id, "translation", "skipped", 75,
                phase_data={"reason": "Text is already in English"}
            )
        
        # Phase 4: Text Preprocessing
        await storage_service.update_processing_status(
            input_id, "preprocessing", "processing", 80
        )
        
        preprocessing_result = await preprocessing_service.preprocess_text(
            processed_text
        )
        
        await storage_service.update_processing_status(
            input_id, "preprocessing", "completed", 100,
            phase_data={"preprocessing_result": preprocessing_result.dict()}
        )
        
        # Update final status
        await storage_service.update_input_record_status(
            input_id, "completed", "preprocessing_complete"
        )
        
        logger.info("Input processing pipeline completed", input_id=input_id)
        
    except Exception as e:
        logger.error("Input processing pipeline failed", 
                    input_id=input_id, 
                    error=str(e))
        
        await storage_service.update_processing_status(
            input_id, "pipeline", "failed", 0,
            error_message=str(e),
            error_details={"exception_type": type(e).__name__}
        )
        
        await storage_service.update_input_record_status(
            input_id, "failed", "pipeline_error"
        )

