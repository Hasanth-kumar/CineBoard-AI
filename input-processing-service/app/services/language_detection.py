"""
Language detection service using langdetect + langid as primary with Google Translate API fallback
"""

import structlog
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
import redis.asyncio as aioredis
from langdetect import detect, DetectorFactory, LangDetectException
import langid
import requests

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
        
        # Initialize Google Translate API endpoint for fallback
        self.google_api_key = settings.GOOGLE_TRANSLATE_API_KEY
        self.google_base_url = "https://translation.googleapis.com/language/translate/v2/detect"
    
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
            # Log as info for expected failures (non-Latin scripts, short text)
            if "Non-Latin script detected" in str(e) or "Text too short" in str(e):
                logger.info("langdetect skipped", reason=str(e))
            else:
                logger.warning("langdetect failed", error=str(e))
        
        # Try secondary detection method (langid)
        try:
            result = await self._detect_with_langid(text)
            if result.confidence >= settings.LANGUAGE_DETECTION_CONFIDENCE_THRESHOLD:
                logger.info("Language detected with langid", 
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
            logger.warning("langid detection failed", error=str(e))
        
        # Try fallback method (Google Translate)
        if self.google_api_key:
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
            
            # Skip langdetect for very short text or non-Latin scripts
            if len(cleaned_text) < 10:
                raise LanguageDetectionError("Text too short for langdetect")
            
            # Check if text contains non-Latin characters (likely Indic languages)
            # langdetect has poor support for Hindi/Unicode text
            if self._contains_non_latin_script(cleaned_text):
                raise LanguageDetectionError("Non-Latin script detected, skipping langdetect")
            
            # Detect language
            try:
                detected_lang = detect(cleaned_text)
            except LangDetectException as e:
                # Re-raise with our custom message
                raise LanguageDetectionError(f"Non-Latin script detected, skipping langdetect: {str(e)}")
            
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
    
    async def _detect_with_langid(self, text: str) -> LanguageDetectionResult:
        """Detect language using langid library"""
        try:
            # Clean text for better detection
            cleaned_text = self._clean_text_for_detection(text)
            
            # Detect language with langid
            langid_result = langid.classify(cleaned_text)
            
            detected_lang = langid_result[0]
            confidence = langid_result[1]
            
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
            raise LanguageDetectionError(f"langid detection failed: {str(e)}")
    
    async def _detect_with_google_translate(self, text: str) -> LanguageDetectionResult:
        """Detect language using Google Translate REST API"""
        try:
            # Clean text for better detection
            cleaned_text = self._clean_text_for_detection(text)
            
            # Detect language using REST API
            params = {
                'key': self.google_api_key,
                'q': cleaned_text
            }
            
            response = requests.post(self.google_base_url, params=params, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            
            if 'data' not in result or 'detections' not in result['data']:
                raise LanguageDetectionError("Invalid API response format")
            
            detection = result['data']['detections'][0][0]
            detected_lang = detection['language']
            confidence = detection.get('confidence', 0.8)
            
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
        # For very short text, minimal cleaning to preserve features
        if len(text) < 20:
            return text.strip()
        
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
    
    def _contains_non_latin_script(self, text: str) -> bool:
        """Check if text contains non-Latin scripts (e.g., Hindi, Arabic, Chinese)"""
        # Check for common non-Latin Unicode ranges
        for char in text:
            # Hindi/Devanagari script (U+0900-U+097F)
            if '\u0900' <= char <= '\u097F':
                return True
            # Arabic script (U+0600-U+06FF)
            elif '\u0600' <= char <= '\u06FF':
                return True
            # Chinese characters (U+4E00-U+9FFF)
            elif '\u4E00' <= char <= '\u9FFF':
                return True
            # Other Indic scripts
            elif '\u0980' <= char <= '\u09FF':  # Bengali
                return True
            elif '\u0A00' <= char <= '\u0A7F':  # Gurmukhi
                return True
            elif '\u0A80' <= char <= '\u0AFF':  # Gujarati
                return True
            elif '\u0B00' <= char <= '\u0B7F':  # Oriya
                return True
            elif '\u0B80' <= char <= '\u0BFF':  # Tamil
                return True
            elif '\u0C00' <= char <= '\u0C7F':  # Telugu
                return True
            elif '\u0C80' <= char <= '\u0CFF':  # Kannada
                return True
            elif '\u0D00' <= char <= '\u0D7F':  # Malayalam
                return True
        
        return False
    
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
