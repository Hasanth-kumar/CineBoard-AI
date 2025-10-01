"""
Language detection service using langdetect + polyglot as primary with Google Translate API fallback
"""

import structlog
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
import aioredis
from langdetect import detect, DetectorFactory, LangDetectException
import polyglot
from polyglot.detect import Detector
import google.cloud.translate_v2 as translate

from app.core.config import settings
from app.core.exceptions import LanguageDetectionError
from app.schemas.input_processing import LanguageDetectionResult
from app.core.redis import CacheService

logger = structlog.get_logger()

# Set seed for consistent results
DetectorFactory.seed = 0


class LanguageDetectionService:
    """Service for detecting language of input text"""
    
    def __init__(self, db: AsyncSession, redis: aioredis.Redis):
        self.db = db
        self.redis = redis
        self.cache_service = CacheService(redis)
        
        # Initialize polyglot detector
        self.polyglot_detector = Detector
        
        # Initialize Google Translate client as fallback if API key is available
        self.google_client = None
        if settings.GOOGLE_TRANSLATE_API_KEY:
            try:
                self.google_client = translate.Client()
                logger.info("Google Translate client initialized as fallback")
            except Exception as e:
                logger.warning("Failed to initialize Google Translate client", error=str(e))
    
    async def detect_language(self, text: str) -> LanguageDetectionResult:
        """
        Detect language of input text with caching and fallback strategies
        """
        logger.info("Starting language detection", text_length=len(text))
        
        # Check cache first
        cache_key = f"lang_detect:{hash(text)}"
        cached_result = await self.cache_service.get(cache_key)
        
        if cached_result:
            logger.info("Language detection result found in cache")
            return LanguageDetectionResult.parse_raw(cached_result)
        
        # Try primary detection method (langdetect)
        try:
            result = await self._detect_with_langdetect(text)
            if result.confidence >= settings.LANGUAGE_DETECTION_CONFIDENCE_THRESHOLD:
                logger.info("Language detected with langdetect", 
                           language=result.language, 
                           confidence=result.confidence)
                
                # Cache the result
                await self.cache_service.set(
                    cache_key, 
                    result.json(), 
                    settings.CACHE_TTL_LANGUAGE_DETECTION
                )
                
                return result
        except Exception as e:
            logger.warning("langdetect failed", error=str(e))
        
        # Try secondary detection method (polyglot)
        try:
            result = await self._detect_with_polyglot(text)
            if result.confidence >= settings.LANGUAGE_DETECTION_CONFIDENCE_THRESHOLD:
                logger.info("Language detected with polyglot", 
                           language=result.language, 
                           confidence=result.confidence)
                
                # Cache the result
                await self.cache_service.set(
                    cache_key, 
                    result.json(), 
                    settings.CACHE_TTL_LANGUAGE_DETECTION
                )
                
                return result
        except Exception as e:
            logger.warning("polyglot detection failed", error=str(e))
        
        # Try fallback method (Google Translate)
        if self.google_client:
            try:
                result = await self._detect_with_google_translate(text)
                logger.info("Language detected with Google Translate", 
                           language=result.language, 
                           confidence=result.confidence)
                
                # Cache the result
                await self.cache_service.set(
                    cache_key, 
                    result.json(), 
                    settings.CACHE_TTL_LANGUAGE_DETECTION
                )
                
                return result
            except Exception as e:
                logger.warning("Google Translate detection failed", error=str(e))
        
        # Fallback to default
        logger.warning("All language detection methods failed, using default")
        result = LanguageDetectionResult(
            language="en",
            confidence=0.5,
            is_reliable=False,
            alternative_languages=[]
        )
        
        return result
    
    async def _detect_with_langdetect(self, text: str) -> LanguageDetectionResult:
        """Detect language using langdetect library"""
        try:
            # Clean text for better detection
            cleaned_text = self._clean_text_for_detection(text)
            
            # Detect language
            detected_lang = detect(cleaned_text)
            
            # Calculate confidence (langdetect doesn't provide confidence directly)
            # We'll use a heuristic based on text length and language support
            confidence = self._calculate_confidence(cleaned_text, detected_lang)
            
            # Check if language is supported
            is_reliable = (
                detected_lang in settings.ALLOWED_LANGUAGES and 
                confidence >= settings.LANGUAGE_DETECTION_CONFIDENCE_THRESHOLD
            )
            
            # Get alternative languages
            alternative_languages = await self._get_alternative_languages(cleaned_text)
            
            return LanguageDetectionResult(
                language=detected_lang,
                confidence=confidence,
                is_reliable=is_reliable,
                alternative_languages=alternative_languages
            )
            
        except LangDetectException as e:
            raise LanguageDetectionError(f"langdetect failed: {str(e)}")
        except Exception as e:
            raise LanguageDetectionError(f"Language detection error: {str(e)}")
    
    async def _detect_with_polyglot(self, text: str) -> LanguageDetectionResult:
        """Detect language using polyglot library"""
        try:
            # Clean text for better detection
            cleaned_text = self._clean_text_for_detection(text)
            
            # Detect language with polyglot
            polyglot_result = self.polyglot_detector(cleaned_text)
            
            detected_lang = polyglot_result.language.code
            confidence = polyglot_result.confidence
            
            # Check if language is supported
            is_reliable = (
                detected_lang in settings.ALLOWED_LANGUAGES and 
                confidence >= settings.LANGUAGE_DETECTION_CONFIDENCE_THRESHOLD
            )
            
            # Get alternative languages
            alternative_languages = await self._get_alternative_languages(cleaned_text)
            
            return LanguageDetectionResult(
                language=detected_lang,
                confidence=confidence,
                is_reliable=is_reliable,
                alternative_languages=alternative_languages
            )
            
        except Exception as e:
            raise LanguageDetectionError(f"polyglot detection failed: {str(e)}")
    
    async def _detect_with_google_translate(self, text: str) -> LanguageDetectionResult:
        """Detect language using Google Translate API"""
        try:
            # Clean text for better detection
            cleaned_text = self._clean_text_for_detection(text)
            
            # Detect language
            result = self.google_client.detect_language(cleaned_text)
            
            detected_lang = result['language']
            confidence = result.get('confidence', 0.8)
            
            # Check if language is supported
            is_reliable = (
                detected_lang in settings.ALLOWED_LANGUAGES and 
                confidence >= settings.LANGUAGE_DETECTION_CONFIDENCE_THRESHOLD
            )
            
            return LanguageDetectionResult(
                language=detected_lang,
                confidence=confidence,
                is_reliable=is_reliable,
                alternative_languages=[]
            )
            
        except Exception as e:
            raise LanguageDetectionError(f"Google Translate detection failed: {str(e)}")
    
    def _clean_text_for_detection(self, text: str) -> str:
        """Clean text for better language detection"""
        # Remove extra whitespace
        cleaned = ' '.join(text.split())
        
        # Remove URLs and email addresses
        import re
        cleaned = re.sub(r'https?://[^\s]+', '', cleaned)
        cleaned = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '', cleaned)
        
        # Remove excessive punctuation
        cleaned = re.sub(r'[!]{3,}', '!', cleaned)
        cleaned = re.sub(r'[?]{3,}', '?', cleaned)
        
        return cleaned.strip()
    
    def _calculate_confidence(self, text: str, language: str) -> float:
        """Calculate confidence score for language detection"""
        # Base confidence
        confidence = 0.8
        
        # Adjust based on text length
        if len(text) < 50:
            confidence -= 0.2
        elif len(text) > 200:
            confidence += 0.1
        
        # Adjust based on language support
        if language not in settings.ALLOWED_LANGUAGES:
            confidence -= 0.3
        
        # Ensure confidence is within bounds
        return max(0.1, min(1.0, confidence))
    
    async def _get_alternative_languages(self, text: str) -> list:
        """Get alternative language suggestions"""
        # This is a simplified implementation
        # In a real implementation, you might use multiple detection methods
        alternatives = []
        
        # Common language pairs for Indian languages
        if len(text) > 20:  # Only for longer texts
            alternatives = [
                {"language": "hi", "confidence": 0.6},
                {"language": "te", "confidence": 0.5},
                {"language": "ta", "confidence": 0.4}
            ]
        
        return alternatives
