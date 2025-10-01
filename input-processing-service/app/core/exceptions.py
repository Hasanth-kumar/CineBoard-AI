"""
Custom exceptions for Input Processing Service
"""

from typing import Optional


class InputProcessingException(Exception):
    """Base exception for input processing errors"""
    
    def __init__(
        self,
        message: str,
        error_code: str = "INPUT_PROCESSING_ERROR",
        status_code: int = 400,
        details: Optional[dict] = None
    ):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(InputProcessingException):
    """Input validation error"""
    
    def __init__(self, message: str, details: Optional[dict] = None):
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            status_code=400,
            details=details
        )


class LanguageDetectionError(InputProcessingException):
    """Language detection error"""
    
    def __init__(self, message: str, details: Optional[dict] = None):
        super().__init__(
            message=message,
            error_code="LANGUAGE_DETECTION_ERROR",
            status_code=500,
            details=details
        )


class TranslationError(InputProcessingException):
    """Translation error"""
    
    def __init__(self, message: str, details: Optional[dict] = None):
        super().__init__(
            message=message,
            error_code="TRANSLATION_ERROR",
            status_code=500,
            details=details
        )


class ContentPolicyError(InputProcessingException):
    """Content policy violation error"""
    
    def __init__(self, message: str, details: Optional[dict] = None):
        super().__init__(
            message=message,
            error_code="CONTENT_POLICY_ERROR",
            status_code=400,
            details=details
        )


class CacheError(InputProcessingException):
    """Cache operation error"""
    
    def __init__(self, message: str, details: Optional[dict] = None):
        super().__init__(
            message=message,
            error_code="CACHE_ERROR",
            status_code=500,
            details=details
        )


class DatabaseError(InputProcessingException):
    """Database operation error"""
    
    def __init__(self, message: str, details: Optional[dict] = None):
        super().__init__(
            message=message,
            error_code="DATABASE_ERROR",
            status_code=500,
            details=details
        )


class RateLimitError(InputProcessingException):
    """Rate limit exceeded error"""
    
    def __init__(self, message: str, details: Optional[dict] = None):
        super().__init__(
            message=message,
            error_code="RATE_LIMIT_ERROR",
            status_code=429,
            details=details
        )

