"""
Translation facade to maintain compatibility when replacing the monolith TranslationService
"""

import structlog
from typing import Optional
import redis.asyncio as aioredis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import TranslationError
from app.core.redis import CacheService
from app.schemas.input_processing import TranslationResult
from .strategy import TranslationStrategy

logger = structlog.get_logger()


class TranslationServiceFacade:
    """Facade that maintains the original TranslationService API while using new provider architecture"""
    
    def __init__(self, db: AsyncSession, redis: aioredis.Redis):
        self.db = db
        self.redis = redis
        self.cache_service = CacheService(redis)
        self.strategy = TranslationStrategy()
    
    async def translate_text(
        self, 
        text: str, 
        source_language: str, 
        target_language: str = None
    ) -> TranslationResult:
        """
        Translate text from source language to target language
        Maintains the exact same API as the original TranslationService
        """
        if target_language is None:
            target_language = settings.DEFAULT_TARGET_LANGUAGE
        
        logger.info("Starting translation", 
                   source_lang=source_language, 
                   target_lang=target_language,
                   text_length=len(text))
        
        # Check cache first
        cache_key = f"translation:{hash(text)}:{source_language}:{target_language}"
        cached_result = await self.cache_service.get(cache_key)
        
        if cached_result:
            logger.info("Translation result found in cache")
            return TranslationResult.parse_raw(cached_result)
        
        try:

            # Use new provider strategy
            result = await self.strategy.translate_with_fallback(
                text, source_language, target_language
            )
            
            logger.info("Translation completed", method=result.method)
            
            # Cache the result
            await self.cache_service.set(
                cache_key, 
                result.json(), 
                settings.CACHE_TTL_TRANSLATION
            )
            
            return result
            
        except Exception as e:
            logger.error("All translation methods failed", error=str(e))
            raise TranslationError(f"Translation failed: {str(e)}")
