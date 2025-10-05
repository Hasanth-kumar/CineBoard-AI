"""
Google Translate provider
"""

import structlog
import requests
import asyncio
from typing import Optional

from app.core.config import settings
from app.core.exceptions import TranslationError
from app.schemas.input_processing import TranslationResult
from .base import TranslationProvider

logger = structlog.get_logger()


class GoogleTranslationProvider(TranslationProvider):
    """Google Translate API provider using REST API"""
    
    def __init__(self):
        self.api_key = settings.GOOGLE_TRANSLATE_API_KEY
        self.base_url = "https://translation.googleapis.com/language/translate/v2"
    
    async def translate(
        self, 
        text: str, 
        source_language: str, 
        target_language: str
    ) -> TranslationResult:
        """Translate using Google Translate REST API"""
        try:
            # Run in thread pool since requests is synchronous
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                self._translate_sync,
                text,
                source_language,
                target_language
            )
            
            return TranslationResult(
                original_text=text,
                translated_text=result['translatedText'],
                source_language=source_language,
                target_language=target_language,
                confidence=result.get('confidence', 0.9),
                method="google_translate"
            )
            
        except Exception as e:
            raise TranslationError(f"Google Translate failed: {str(e)}")
    
    def _translate_sync(
        self, 
        text: str, 
        source_language: str, 
        target_language: str
    ):
        """Synchronous translation call using REST API"""
        if not self.api_key:
            raise TranslationError("Google Translate API key not configured")
        
        params = {
            'key': self.api_key,
            'q': text,
            'source': source_language,
            'target': target_language
        }
        
        response = requests.post(self.base_url, params=params, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        
        if 'data' not in result or 'translations' not in result['data']:
            raise TranslationError("Invalid API response format")
        
        translation = result['data']['translations'][0]
        return {
            'translatedText': translation['translatedText'],
            'confidence': translation.get('confidence', 0.9)
        }
    
    async def is_available(self) -> bool:
        """Check if Google Translate is available"""
        return self.api_key is not None
    
    def get_provider_name(self) -> str:
        """Get provider name"""
        return "google_translate"
