"""
Tests for input processing pipeline workflow
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi import BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
import redis.asyncio as aioredis

from app.workflows.pipeline import process_input_pipeline
from app.schemas.input_processing import (
    InputValidationResponse,
    LanguageDetectionResult,
    TranslationResult,
    TextPreprocessingResult,
    ProcessingPhase,
    ProcessingStatus
)


@pytest.fixture
def mock_db():
    """Mock database session"""
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def mock_redis():
    """Mock Redis connection"""
    return AsyncMock(spec=aioredis.Redis)


@pytest.mark.asyncio
async def test_process_input_pipeline_success(mock_db, mock_redis):
    """Test successful input processing pipeline"""
    # Mock services
    with patch.multiple(
        'app.workflows.pipeline',
        InputValidationService=MagicMock(),
        LanguageDetectionService=MagicMock(),
        TranslationService=MagicMock(),
        TextPreprocessingService=MagicMock(),
        InputStorageService=MagicMock()
    ) as mocked_services:
        
        # Setup mock service instances and their methods
        validation_instance = AsyncMock()
        validation_instance.validate_input.return_value = InputValidationResponse(
            validation_id="test-validation-id",
            status="valid",
            input_length=10,
            detected_content_types=[],
            detected_sensitive_content=[]
        )
        mocked_services['InputValidationService'].return_value = validation_instance
        
        language_instance = AsyncMock()
        language_instance.detect_language.return_value = LanguageDetectionResult(
            language="en",
            confidence=0.95,
            detected_script="Latin",
            language_name="English"
        )
        mocked_services['LanguageDetectionService'].return_value = language_instance
        
        translation_instance = AsyncMock()
        translation_instance.translate_text.return_value = TranslationResult(
            original_text="Hello world",
            translated_text="Hello world",
            source_language="en",
            target_language="en",
            confidence=0.95,
            method="google_translate"
        )
        mocked_services['TranslationService'].return_value = translation_instance
        
        preprocessing_instance = AsyncMock()
        preprocessing_instance.preprocess_text.return_value = TextPreprocessingResult(
            processed_text="Hello world",
            original_text="Hello world",
            preprocessing_steps=[]
        )
        mocked_services['TextPreprocessingService'].return_value = preprocessing_instance
        
        storage_instance = AsyncMock()
        storage_instance.update_processing_status.return_value = True
        storage_instance.update_input_record_status.return_value = True
        mocked_services['InputStorageService'].return_value = storage_instance
        
        # Run pipeline
        await process_input_pipeline(1, "Hello world", 123, mock_db, mock_redis)
        
        # Verify validation was called
        assert validation_instance.validate_input.called
        
        # Verify language detection was called
        assert language_instance.detect_language.called
        
        # Verify preprocessing was called
        assert preprocessing_instance.preprocess_text.called


@pytest.mark.asyncio
async def test_process_input_pipeline_validation_failure(mock_db, mock_redis):
    """Test pipeline failure due to validation"""
    with patch.multiple(
        'app.workflows.pipeline',
        InputValidationService=MagicMock(),
        InputStorageService=MagicMock()
    ) as mocked_services:
        
        # Setup validation failure
        validation_instance = AsyncMock()
        validation_instance.validate_input.return_value = InputValidationResponse(
            validation_id="test-validation-id",
            status="invalid",
            input_length=10,
            detected_content_types=[],
            detected_sensitive_content=[]
        )
        mocked_services['InputValidationService'].return_value = validation_instance
        
        storage_instance = AsyncMock()
        mocked_services['InputStorageService'].return_value = storage_instance
        
        # Run pipeline
        await process_input_pipeline(1, "Invalid content", 123, mock_db, mock_redis)
        
        # Verify validation was called
        assert validation_instance.validate_input.called
        
        # Verify status was updated to failed
        assert storage_instance.update_processing_status.called


@pytest.mark.asyncio
async def test_process_input_pipeline_exception_handling(mock_db, mock_redis):
    """Test pipeline exception handling"""
    with patch.multiple(
        'app.workflows.pipeline',
        InputValidationService=MagicMock()
    ) as mocked_services:
        
        # Setup service to raise exception
        validation_instance = AsyncMock()
        validation_instance.validate_input.side_effect = Exception("Service error")
        mocked_services['InputValidationService'].return_value = validation_instance
        
        with patch('app.workflows.pipeline.InputStorageService') as mock_storage:
            storage_instance = AsyncMock()
            mock_storage.return_value = storage_instance
            
            # Run pipeline
            await process_input_pipeline(1, "Test text", 123, mock_db, mock_redis)
            
            # Verify error status was updated
            assert storage_instance.update_processing_status.called
            assert storage_instance.update_input_record_status.called
