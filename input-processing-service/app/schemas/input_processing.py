"""
Pydantic schemas for Input Processing Service
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


class ProcessingStatus(str, Enum):
    """Processing status enumeration"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class ProcessingPhase(str, Enum):
    """Processing phase enumeration"""
    VALIDATION = "validation"
    LANGUAGE_DETECTION = "language_detection"
    TRANSLATION = "translation"
    PREPROCESSING = "preprocessing"


class ValidationStatus(str, Enum):
    """Validation status enumeration"""
    VALID = "valid"
    INVALID = "invalid"
    PENDING = "pending"


# Request Schemas
class InputValidationRequest(BaseModel):
    """Request schema for input validation"""
    text: str = Field(..., min_length=1, max_length=2000, description="Input text to validate")
    user_id: Optional[int] = Field(None, description="User ID for validation context")
    session_id: Optional[str] = Field(None, description="Session ID for tracking")
    
    @validator('text')
    def validate_text(cls, v):
        if not v.strip():
            raise ValueError('Text cannot be empty or only whitespace')
        return v.strip()


class InputProcessingRequest(BaseModel):
    """Request schema for complete input processing"""
    text: str = Field(..., min_length=1, max_length=2000, description="Input text to process")
    user_id: int = Field(..., description="User ID")
    session_id: Optional[str] = Field(None, description="Session ID for tracking")
    target_language: Optional[str] = Field("en", description="Target language for translation")
    
    @validator('text')
    def validate_text(cls, v):
        if not v.strip():
            raise ValueError('Text cannot be empty or only whitespace')
        return v.strip()


# Response Schemas
class ValidationResult(BaseModel):
    """Validation result details"""
    is_valid: bool
    errors: List[str] = []
    warnings: List[str] = []
    content_policy_check: Dict[str, Any] = {}
    length_check: Dict[str, Any] = {}
    format_check: Dict[str, Any] = {}


class InputValidationResponse(BaseModel):
    """Response schema for input validation"""
    validation_id: str
    status: ValidationStatus
    validation_result: ValidationResult
    message: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class LanguageDetectionResult(BaseModel):
    """Language detection result"""
    language: str
    confidence: float
    is_reliable: bool
    alternative_languages: List[Dict[str, Any]] = []


class TranslationResult(BaseModel):
    """Translation result"""
    original_text: str
    translated_text: str
    source_language: str
    target_language: str
    confidence: float
    method: str  # "google_translate", "nllb_200", "gpt4"


class PreprocessingResult(BaseModel):
    """Text preprocessing result"""
    original_text: str
    processed_text: str
    preprocessing_steps: List[str] = []
    metadata: Dict[str, Any] = {}


class ProcessingPhaseStatus(BaseModel):
    """Status of a processing phase"""
    phase: ProcessingPhase
    status: ProcessingStatus
    progress_percentage: int = Field(..., ge=0, le=100)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[int] = None
    phase_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    error_details: Optional[Dict[str, Any]] = None


class InputProcessingResponse(BaseModel):
    """Response schema for input processing"""
    input_id: int
    status: ProcessingStatus
    current_phase: Optional[ProcessingPhase] = None
    progress_percentage: int = Field(default=0, ge=0, le=100)
    phases: List[ProcessingPhaseStatus] = []
    message: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ProcessingStatusResponse(BaseModel):
    """Response schema for processing status"""
    input_id: int
    status: ProcessingStatus
    current_phase: Optional[ProcessingPhase] = None
    progress_percentage: int = Field(..., ge=0, le=100)
    phases: List[ProcessingPhaseStatus] = []
    created_at: datetime
    updated_at: datetime
    processed_at: Optional[datetime] = None


# Internal Schemas
class InputRecordCreate(BaseModel):
    """Schema for creating input record"""
    user_id: int
    raw_input: str
    session_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


class ProcessingStatusCreate(BaseModel):
    """Schema for creating processing status"""
    input_record_id: int
    phase: ProcessingPhase
    status: ProcessingStatus
    progress_percentage: int = 0
    phase_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    error_details: Optional[Dict[str, Any]] = None


class ProcessingStatusUpdate(BaseModel):
    """Schema for updating processing status"""
    status: Optional[ProcessingStatus] = None
    progress_percentage: Optional[int] = None
    phase_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    error_details: Optional[Dict[str, Any]] = None
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[int] = None

