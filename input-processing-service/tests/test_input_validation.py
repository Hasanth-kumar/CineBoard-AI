"""
Tests for input validation service
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from app.services.input_validation import InputValidationService
from app.core.exceptions import ValidationError


@pytest.fixture
def validation_service():
    """Create validation service instance for testing"""
    db = AsyncMock()
    redis = AsyncMock()
    return InputValidationService(db, redis)


@pytest.mark.asyncio
async def test_validate_input_success(validation_service):
    """Test successful input validation"""
    text = "This is a valid input text for testing purposes."
    
    result = await validation_service.validate_input(text)
    
    assert result.is_valid is True
    assert len(result.errors) == 0
    assert result.length_check["is_valid"] is True


@pytest.mark.asyncio
async def test_validate_input_too_short(validation_service):
    """Test validation with text that's too short"""
    text = "Short"
    
    result = await validation_service.validate_input(text)
    
    assert result.is_valid is False
    assert len(result.errors) > 0
    assert "too short" in result.errors[0].lower()


@pytest.mark.asyncio
async def test_validate_input_too_long(validation_service):
    """Test validation with text that's too long"""
    text = "x" * 3000  # Exceeds MAX_INPUT_LENGTH
    
    result = await validation_service.validate_input(text)
    
    assert result.is_valid is False
    assert len(result.errors) > 0
    assert "too long" in result.errors[0].lower()


@pytest.mark.asyncio
async def test_validate_input_content_policy_violation(validation_service):
    """Test validation with content policy violation"""
    text = "This text contains violence and explicit content."
    
    result = await validation_service.validate_input(text)
    
    assert result.is_valid is False
    assert len(result.errors) > 0
    assert "content policy" in result.errors[0].lower()


@pytest.mark.asyncio
async def test_validate_input_format_issues(validation_service):
    """Test validation with format issues"""
    text = "   Text with leading spaces   \n\n\n\nMultiple newlines"
    
    result = await validation_service.validate_input(text)
    
    # Should still be valid but with warnings
    assert result.is_valid is True
    assert len(result.errors) == 0


@pytest.mark.asyncio
async def test_validate_input_encoding_issues(validation_service):
    """Test validation with encoding issues"""
    text = "Text with invalid \x00 control character"
    
    result = await validation_service.validate_input(text)
    
    assert result.is_valid is False
    assert len(result.errors) > 0
    assert "control character" in result.errors[0].lower()

