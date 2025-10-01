"""
Configuration management for Input Processing Service
"""

from pydantic_settings import BaseSettings
from typing import List, Optional
import os


class Settings(BaseSettings):
    """Application settings"""
    
    # Service Configuration
    SERVICE_NAME: str = "input-processing-service"
    SERVICE_VERSION: str = "1.0.0"
    SERVICE_PORT: int = 8002
    DEBUG: bool = False
    
    # Database Configuration
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/input_processing"
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # API Keys
    GOOGLE_TRANSLATE_API_KEY: Optional[str] = None
    HUGGINGFACE_API_KEY: Optional[str] = None
    
    # Model Endpoints
    INDIC_TRANS2_ENDPOINT: Optional[str] = None  # HuggingFace Inference API or self-hosted
    NLLB_ENDPOINT: Optional[str] = None  # HuggingFace Inference API or self-hosted
    
    # Security
    JWT_SECRET: str = "your-jwt-secret-key"
    ENCRYPTION_KEY: str = "your-encryption-key"
    
    # CORS Configuration
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:3001",
        "https://app.videogen.com",
        "https://admin.videogen.com"
    ]
    ALLOWED_HOSTS: List[str] = ["*"]
    
    # Logging Configuration
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 100
    RATE_LIMIT_PER_HOUR: int = 1000
    
    # Cache Configuration
    CACHE_TTL_TRANSLATION: int = 3600  # 1 hour
    CACHE_TTL_LANGUAGE_DETECTION: int = 1800  # 30 minutes
    CACHE_TTL_VALIDATION: int = 300  # 5 minutes
    
    # Input Validation Configuration
    MIN_INPUT_LENGTH: int = 10
    MAX_INPUT_LENGTH: int = 2000
    ALLOWED_LANGUAGES: List[str] = [
        "en", "hi", "te", "ta", "bn", "gu", "mr", "kn", "ml", "or", "pa"
    ]
    
    # Monitoring Configuration
    PROMETHEUS_PORT: int = 9090
    METRICS_ENABLED: bool = True
    
    # Content Policy Configuration
    FORBIDDEN_CONTENT_KEYWORDS: List[str] = [
        "violence", "explicit", "hate_speech", "spam", "malicious"
    ]
    
    # Translation Configuration
    DEFAULT_TARGET_LANGUAGE: str = "en"
    TRANSLATION_CONFIDENCE_THRESHOLD: float = 0.8
    
    # Language Detection Configuration
    LANGUAGE_DETECTION_CONFIDENCE_THRESHOLD: float = 0.8
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()

