"""
Input validation service for content policy, length, and format validation
"""

import re
import structlog
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
import redis.asyncio as aioredis

from app.core.config import settings
from app.core.exceptions import ValidationError, ContentPolicyError
from app.schemas.input_processing import ValidationResult, ValidationStatus

logger = structlog.get_logger()


class InputValidationService:
    """Service for validating user input"""
    
    def __init__(self, db: AsyncSession, redis: aioredis.Redis):
        self.db = db
        self.redis = redis
    
    async def validate_input(
        self, 
        text: str, 
        user_id: int = None, 
        session_id: str = None
    ) -> ValidationResult:
        """
        Validate input text for content policy, length, and format
        """
        logger.info("Starting input validation", 
                   text_length=len(text), 
                   user_id=user_id)
        
        errors = []
        warnings = []
        
        # Length validation
        length_check = await self._validate_length(text)
        if not length_check["is_valid"]:
            errors.extend(length_check["errors"])
        
        # Format validation
        format_check = await self._validate_format(text)
        if not format_check["is_valid"]:
            errors.extend(format_check["errors"])
        
        # Content policy validation
        content_policy_check = await self._validate_content_policy(text)
        if not content_policy_check["is_valid"]:
            errors.extend(content_policy_check["errors"])
        
        # Character encoding validation
        encoding_check = await self._validate_encoding(text)
        if not encoding_check["is_valid"]:
            errors.extend(encoding_check["errors"])
        
        is_valid = len(errors) == 0
        
        result = ValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            content_policy_check=content_policy_check,
            length_check=length_check,
            format_check=format_check
        )
        
        logger.info("Input validation completed", 
                   is_valid=is_valid, 
                   error_count=len(errors))
        
        return result
    
    async def _validate_length(self, text: str) -> Dict[str, Any]:
        """Validate text length"""
        length = len(text.strip())
        
        if length < settings.MIN_INPUT_LENGTH:
            return {
                "is_valid": False,
                "errors": [f"Text too short. Minimum length: {settings.MIN_INPUT_LENGTH} characters"],
                "actual_length": length,
                "min_length": settings.MIN_INPUT_LENGTH
            }
        
        if length > settings.MAX_INPUT_LENGTH:
            return {
                "is_valid": False,
                "errors": [f"Text too long. Maximum length: {settings.MAX_INPUT_LENGTH} characters"],
                "actual_length": length,
                "max_length": settings.MAX_INPUT_LENGTH
            }
        
        return {
            "is_valid": True,
            "actual_length": length,
            "min_length": settings.MIN_INPUT_LENGTH,
            "max_length": settings.MAX_INPUT_LENGTH
        }
    
    async def _validate_format(self, text: str) -> Dict[str, Any]:
        """Validate text format"""
        errors = []
        
        # Check for excessive whitespace
        if len(text) != len(text.strip()):
            errors.append("Text contains leading or trailing whitespace")
        
        # Check for excessive line breaks
        line_breaks = text.count('\n')
        if line_breaks > 10:  # Allow reasonable number of line breaks
            errors.append("Text contains too many line breaks")
        
        # Check for excessive repeated characters
        if re.search(r'(.)\1{10,}', text):  # Same character repeated 10+ times
            errors.append("Text contains excessive repeated characters")
        
        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "line_breaks": line_breaks
        }
    
    async def _validate_content_policy(self, text: str) -> Dict[str, Any]:
        """Validate content policy compliance"""
        errors = []
        warnings = []
        
        text_lower = text.lower()
        
        # Check for forbidden keywords
        for keyword in settings.FORBIDDEN_CONTENT_KEYWORDS:
            if keyword in text_lower:
                errors.append(f"Content policy violation: '{keyword}' detected")
        
        # Check for spam patterns
        spam_patterns = [
            r'https?://[^\s]+',  # URLs
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # Email addresses
            r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',  # Phone numbers
        ]
        
        for pattern in spam_patterns:
            if re.search(pattern, text):
                warnings.append(f"Potential spam content detected: {pattern}")
        
        # Check for excessive capitalization
        caps_ratio = sum(1 for c in text if c.isupper()) / len(text) if text else 0
        if caps_ratio > 0.5:  # More than 50% uppercase
            warnings.append("Excessive capitalization detected")
        
        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "caps_ratio": caps_ratio
        }
    
    async def _validate_encoding(self, text: str) -> Dict[str, Any]:
        """Validate character encoding"""
        errors = []
        
        try:
            # Try to encode/decode to check for valid UTF-8
            text.encode('utf-8').decode('utf-8')
        except UnicodeError as e:
            errors.append(f"Invalid character encoding: {str(e)}")
        
        # Check for control characters (except common ones like \n, \t, \r)
        control_chars = [c for c in text if ord(c) < 32 and c not in '\n\t\r']
        if control_chars:
            errors.append("Text contains invalid control characters")
        
        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "control_chars_found": len(control_chars)
        }

