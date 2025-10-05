"""
Translation strategy for managing provider fallback chain
"""

import structlog
from typing import List, Optional
from app.core.exceptions import TranslationError
from app.schemas.input_processing import TranslationResult
from .providers import (
    TranslationProvider,
    GoogleTranslationProvider,
    # TODO (Production Phase): Re-enable IndicTrans2 as Fallback Layer 1
    # IndicTranslator,
    NLLBTranslator,
    # HuggingFaceTranslator - REMOVED for MVP (2-layer system)
)

logger = structlog.get_logger()


class TranslationStrategy:
    """Manages translation provider fallback strategy"""
    
    def __init__(self):
        self.providers: List[TranslationProvider] = []
        self._initialize_providers()
    
    def _initialize_providers(self):
        """Initialize providers in priority order - MVP 2-layer system"""
        # Google Translate - highest priority (most reliable and fastest)
        self.providers.append(GoogleTranslationProvider())
        
        # TODO (Production Phase): Re-enable IndicTrans2 as Fallback Layer 1
        # IndicTrans2 - second priority for Indic languages (commented out for MVP)
        # self.providers.append(IndicTranslator())
        
        # NLLB-200 - final fallback for all languages
        self.providers.append(NLLBTranslator())
        
        logger.info(f"Initialized {len(self.providers)} translation providers (MVP 2-layer system)")
    
    async def translate_with_fallback(
        self,
        text: str,
        source_language: str,
        target_language: str
    ) -> TranslationResult:
        """
        Translate text using fallback strategy - MVP 2-layer system:
        1. Google Translate (most reliable)
        2. NLLB-200 (general purpose fallback)
        
        TODO (Production Phase): Re-enable IndicTrans2 as Fallback Layer 1
        Future 3-layer system: Google → IndicTrans2 → NLLB
        """
        logger.info(
            "Starting translation with fallback strategy",
            text_length=len(text),
            source_lang=source_language,
            target_lang=target_language
        )
        
        last_error = None
        
        for provider in self.providers:
            try:
                # Check if provider is available
                if not await provider.is_available():
                    logger.warning(
                        f"Provider {provider.get_provider_name()} is not available, skipping"
                    )
                    continue
                
                logger.info(f"Attempting translation with {provider.get_provider_name()}")
                
                # Try translation with this provider
                result = await provider.translate(text, source_language, target_language)
                
                logger.info(f"Translation successful with {provider.get_provider_name()}")
                return result
                
            except Exception as e:
                last_error = e
                logger.warning(
                    f"Translation failed with {provider.get_provider_name()}",
                    error=str(e)
                )
                continue
        
        # If all providers failed
        logger.error("All translation providers failed")
        raise TranslationError(f"Translation failed: {str(last_error)}")
    
    async def get_available_providers(self) -> List[str]:
        """Get list of available provider names"""
        available = []
        for provider in self.providers:
            if await provider.is_available():
                available.append(provider.get_provider_name())
        return available
    
    async def test_provider(self, provider_name: str) -> bool:
        """Test if a specific provider is working"""
        for provider in self.providers:
            if provider.get_provider_name() == provider_name:
                return await provider.is_available()
        return False
