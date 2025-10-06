"""
Input processing pipeline workflow
"""

from fastapi import BackgroundTasks
import structlog
import redis.asyncio as aioredis

from app.core.database import AsyncSessionLocal
from app.core.redis import get_redis
from app.services.input_validation import InputValidationService
from app.services.language_detection import LanguageDetectionService
from app.services.translation import TranslationService
from app.services.text_preprocessing import TextPreprocessingService
from app.services.storage_facade import InputStorageService
from app.schemas.input_processing import ProcessingPhase, ProcessingStatus

logger = structlog.get_logger()


async def process_input_pipeline(
    input_id: int,
    text: str,
    user_id: int
):
    """
    Background task for processing input through the complete pipeline
    Creates its own database and Redis sessions since request sessions are closed
    """
    logger.info("Starting input processing pipeline", 
                input_id=input_id, 
                text_length=len(text),
                user_id=user_id)
    print(f"DEBUG: Pipeline started for input_id={input_id}, text='{text[:50]}...'")
    print(f"DEBUG: Text bytes: {text.encode('utf-8')}")
    print(f"DEBUG: Text repr: {repr(text)}")
    
    # Create new database session for background task
    async with AsyncSessionLocal() as db:
        # Create new Redis connection for background task
        redis = await get_redis()
        
        try:
            # Initialize services with new sessions
            validation_service = InputValidationService(db, redis)
            language_service = LanguageDetectionService(db, redis)
            translation_service = TranslationService(db, redis)
            preprocessing_service = TextPreprocessingService(db, redis)
            storage_service = InputStorageService(db, redis)
            
            logger.info("Services initialized, starting validation phase", input_id=input_id)
            
            # Phase 1: Validation
            await storage_service.update_processing_status(
                input_id, ProcessingPhase.VALIDATION, ProcessingStatus.PROCESSING, 10
            )
            
            validation_result = await validation_service.validate_input(
                text=text, user_id=user_id
            )
            
            if not validation_result.is_valid:
                await storage_service.update_processing_status(
                    input_id, ProcessingPhase.VALIDATION, ProcessingStatus.FAILED, 0,
                    error_message="Validation failed",
                    error_details={"validation_result": validation_result.dict()}
                )
                return
            
            await storage_service.update_processing_status(
                input_id, ProcessingPhase.VALIDATION, ProcessingStatus.COMPLETED, 25
            )
            
            # Phase 2: Language Detection
            logger.info("Starting language detection phase", input_id=input_id)
            await storage_service.update_processing_status(
                input_id, ProcessingPhase.LANGUAGE_DETECTION, ProcessingStatus.PROCESSING, 30
            )
            
            language_result = await language_service.detect_language(text)
            print(f"DEBUG: Language detected: {language_result.language}, confidence: {language_result.confidence}")
            
            # Store language detection results in input record
            await storage_service.update_language_detection_results(
                input_id, 
                language_result.language, 
                language_result.confidence
            )
            
            await storage_service.update_processing_status(
                input_id, ProcessingPhase.LANGUAGE_DETECTION, ProcessingStatus.COMPLETED, 50,
                phase_data={"language_result": language_result.dict()}
            )
            
            # Phase 3: Translation (if needed)
            processed_text = text
            if language_result.language != "en":
                logger.info("Starting translation phase", 
                           input_id=input_id, 
                           source_lang=language_result.language)
                await storage_service.update_processing_status(
                    input_id, ProcessingPhase.TRANSLATION, ProcessingStatus.PROCESSING, 60
                )
                
                translation_result = await translation_service.translate_text(
                    text, language_result.language, "en"
                )
                
                processed_text = translation_result.translated_text
                
                # Store translation results in input record
                await storage_service.update_translation_results(
                    input_id, 
                    translation_result.dict()
                )
                
                logger.info("Translation completed", 
                           input_id=input_id, 
                           method=translation_result.method)
                
                await storage_service.update_processing_status(
                    input_id, ProcessingPhase.TRANSLATION, ProcessingStatus.COMPLETED, 75,
                    phase_data={"translation_result": translation_result.dict()}
                )
            else:
                logger.info("Translation skipped - text already in English", input_id=input_id)
                await storage_service.update_processing_status(
                    input_id, ProcessingPhase.TRANSLATION, ProcessingStatus.SKIPPED, 75,
                    phase_data={"reason": "Text is already in English"}
                )
            
            # Phase 4: Text Preprocessing
            logger.info("Starting preprocessing phase", input_id=input_id)
            await storage_service.update_processing_status(
                input_id, ProcessingPhase.PREPROCESSING, ProcessingStatus.PROCESSING, 80
            )
            
            preprocessing_result = await preprocessing_service.preprocess_text(
                processed_text
            )
            
            logger.info("Preprocessing completed", input_id=input_id)
            await storage_service.update_processing_status(
                input_id, ProcessingPhase.PREPROCESSING, ProcessingStatus.COMPLETED, 100,
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
            
            # Try to update status with error information
            try:
                await storage_service.update_processing_status(
                    input_id, ProcessingPhase.VALIDATION, ProcessingStatus.FAILED, 0,
                    error_message=str(e),
                    error_details={"exception_type": type(e).__name__}
                )
                
                await storage_service.update_input_record_status(
                    input_id, "failed", "pipeline_error"
                )
            except Exception as status_error:
                logger.error("Failed to update error status", 
                            input_id=input_id, 
                            error=str(status_error))
