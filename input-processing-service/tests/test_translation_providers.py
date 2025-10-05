"""
Tests for translation providers architecture
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from app.services.translation.providers import (
    GoogleTranslationProvider,
    # TODO (Production Phase): Re-enable IndicTrans2 as Fallback Layer 1
    # IndicTranslator,
    NLLBTranslator,
    # HuggingFaceTranslator - REMOVED for MVP (2-layer system)
)
from app.services.translation.strategy import TranslationStrategy
from app.core.exceptions import TranslationError
from app.schemas.input_processing import TranslationResult


@pytest.mark.asyncio
async def test_google_translator_success():
    """Test successful Google Translate translation"""
    provider = GoogleTranslationProvider()
    
    # Mock Google client
    provider.client = MagicMock()
    provider.client.translate.return_value = {
        'translatedText': 'Hello world',
        'confidence': 0.95
    }
    
    result = await provider.translate("Hello world", "en", "es")
    
    assert result.translated_text == "Hello world"
    assert result.method == "google_translate"
    assert result.confidence == 0.95


@pytest.mark.asyncio
async def test_google_translator_not_available():
    """Test Google Translate when not available"""
    provider = GoogleTranslationProvider()
    
    # No client initialized
    provider.client = None
    
    is_available = await provider.is_available()
    assert not is_available


# TODO (Production Phase): Re-enable IndicTrans2 as Fallback Layer 1
# @pytest.mark.asyncio
# async def test_indic_translator_api_success():
#     """Test successful IndicTrans2 API translation"""
#     provider = IndicTranslator()
#     provider.endpoint = "https://api.example.com/translate"
#     
#     with pytest.Mock() as requests:
#         # Mock successful API response
#         response = MagicMock()
#         response.json.return_value = {"translated_text": "Hello world"}
#         response.raise_for_status.return_value = None
#         
#         provider._translate_with_api = AsyncMock(return_value="Hello world")
#         
#         result = await provider.translate("Hello world", "hi", "en")
#         
#         assert result.translated_text == "Hello world"
#         assert result.method == "indic_trans2"


@pytest.mark.asyncio
async def test_nllb_translator_api_success():
    """Test successful NLLB API translation"""
    provider = NLLBTranslator()
    provider.endpoint = "https://api.example.com/nllb"
    
    provider._translate_with_api = AsyncMock(return_value="Hello world")
    
    result = await provider.translate("Hello world", "ne", "en")
    
    assert result.translated_text == "Hello world"
    assert result.method == "nllb_200"


@pytest.mark.asyncio
async def test_translation_strategy_fallback():
    """Test translation strategy with provider fallback - MVP 2-layer system"""
    strategy = TranslationStrategy()
    
    # Mock providers to simulate fallback chain (Google → NLLB)
    with pytest.Mock():
        provider1 = AsyncMock()
        provider1.get_provider_name.return_value = "google_translate"
        provider1.is_available.return_value = False
        provider1.translate.side_effect = Exception("Google failed")
        
        provider2 = AsyncMock()
        provider2.get_provider_name.return_value = "nllb_200"
        provider2.is_available.return_value = True
        provider2.translate.return_value = TranslationResult(
            original_text="Hello",
            translated_text="Hello",
            source_language="hi", 
            target_language="en",
            confidence=0.75,
            method="nllb_200"
        )
        
        strategy.providers = [provider1, provider2]
        
        result = await strategy.translate_with_fallback("Hello", "hi", "en")
        
        assert result.method == "nllb_200"
        assert not provider1.translate.called  # Should have failed
        assert provider2.translate.called


@pytest.mark.asyncio
async def test_translation_strategy_all_providers_fail():
    """Test translation strategy when all providers fail"""
    strategy = TranslationStrategy()
    
    # Mock all providers to fail
    with pytest.Mock():
        for provider in strategy.providers:
            provider.is_available.return_value = False
        
        with pytest.raises(TranslationError):
            await strategy.translate_with_fallback("Hello", "hi", "en")


# HuggingFaceTranslator test - REMOVED for MVP (2-layer system)
# @pytest.mark.asyncio
# async def test_huggingface_translator_success():
#     """Test successful HuggingFace local translation"""
#     provider = HuggingFaceTranslator("facebook/nllb-200-distilled-600M")
#     
#     # Mock model components
#     provider.tokenizer = MagicMock()
#     provider.tokenizer.encode.return_value = [[1, 2, 3]]
#     provider.tokenizer.decode.return_value = "Hello world"
#     
#     provider.model = MagicMock()
#     
#     with pytest.Mock() as torch:
#         outputs = MagicMock()
#         outputs.__getitem__ = MagicMock(return_value=[1, 2, 3])
#         provider.model.generate.return_value = outputs
#         
#         # Simulate available GPU/CPU
#         torch.cuda.is_available.return_value = True
#         
#         result = await provider.translate("Hello world", "ne", "en")
#         
#         assert result.translated_text == "Hello world"
#         assert result.method.startswith("huggingface_")
