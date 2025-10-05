"""
NLLB-200 translation provider
"""

import structlog
import requests
import json
import asyncio
from typing import Optional

from app.core.config import settings
from app.core.exceptions import TranslationError
from app.schemas.input_processing import TranslationResult
from .base import TranslationProvider

logger = structlog.get_logger()


class NLLBTranslator(TranslationProvider):
    """NLLB-200 model provider for multilingual translation"""
    
    def __init__(self):
        self.endpoint = settings.NLLB_ENDPOINT
    
    async def translate(
        self, 
        text: str, 
        source_language: str, 
        target_language: str
    ) -> TranslationResult:
        """Translate using NLLB-200 model"""
        try:
            cleaned_text = self._clean_text_for_translation(text)
            
            if self.endpoint:
                # Use API endpoint
                result = await self._translate_with_api(
                    cleaned_text, source_language, target_language
                )
            else:
                raise TranslationError("NLLB endpoint not configured")
            
            return TranslationResult(
                original_text=text,
                translated_text=result,
                source_language=source_language,
                target_language=target_language,
                confidence=0.75,  # NLLB confidence
                method="nllb_200"
            )
                
        except Exception as e:
            raise TranslationError(f"NLLB translation failed: {str(e)}")
    
    async def _translate_with_api(
        self,
        text: str,
        source_language: str,
        target_language: str
    ) -> str:
        """Translate using NLLB API endpoint"""
        payload = {
            "text": text,
            "source": source_language,
            "target": target_language
        }
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {settings.HUGGINGFACE_API_KEY}"
        }
        
        try:
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: requests.post(
                    self.endpoint,
                    json=payload,
                    headers=headers,
                    timeout=30
                )
            )
            
            response.raise_for_status()
            
            result = response.json()
            
            if isinstance(result, dict) and "translated_text" in result:
                return result["translated_text"]
            elif isinstance(result, list) and len(result) > 0:
                return str(result[0])
            else:
                raise TranslationError(f"Unexpected API response format: {result}")
                
        except requests.RequestException as e:
            raise TranslationError(f"API request failed: {str(e)}")
    
    def _clean_text_for_translation(self, text: str) -> str:
        """Clean text for better translation results"""
        # Remove excessive whitespace and normalize
        cleaned = " ".join(text.strip().split())
        return cleaned.strip()
    
    async def is_available(self) -> bool:
        """Check if NLLB is available"""
        return (
            self.endpoint is not None and 
            settings.HUGGINGFACE_API_KEY is not None
        )
    
    def get_provider_name(self) -> str:
        """Get provider name"""
        return "nllb_200"