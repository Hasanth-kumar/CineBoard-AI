"""
Tests for translation service with Google → IndicTrans2 → NLLB fallback chain
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.translation import TranslationService
from app.core.exceptions import TranslationError
from app.schemas.input_processing import TranslationResult


@pytest.fixture
def translation_service():
    """Create translation service instance for testing"""
    db = AsyncMock()
    redis = AsyncMock()
    return TranslationService(db, redis)


@pytest.mark.asyncio
async def test_translate_text_google_success(translation_service):
    """Test successful translation with Google Translate"""
    # Mock Google Translate client
    translation_service.google_client = MagicMock()
    translation_service.google_client.translate.return_value = {
        'translatedText': 'Hello world',
        'confidence': 0.95
    }
    
    result = await translation_service.translate_text(
        "नमस्ते दुनिया", "hi", "en"
    )
    
    assert result.translated_text == "Hello world"
    assert result.method == "google_translate"
    assert result.confidence == 0.95


@pytest.mark.asyncio
async def test_translate_text_google_fallback_to_indic_trans2(translation_service):
    """Test fallback from Google to IndicTrans2 when Google fails"""
    # Mock Google Translate failure
    translation_service.google_client = MagicMock()
    translation_service.google_client.translate.side_effect = Exception("Google API error")
    
    # Mock IndicTrans2 success
    with patch.object(translation_service, '_translate_with_indic_trans2') as mock_indic:
        mock_indic.return_value = TranslationResult(
            original_text="नमस्ते दुनिया",
            translated_text="Hello world",
            source_language="hi",
            target_language="en",
            confidence=0.8,
            method="indic_trans2_local"
        )
        
        result = await translation_service.translate_text(
            "नमस्ते दुनिया", "hi", "en"
        )
        
        assert result.translated_text == "Hello world"
        assert result.method == "indic_trans2_local"
        assert result.confidence == 0.8


@pytest.mark.asyncio
async def test_translate_text_indic_trans2_fallback_to_nllb(translation_service):
    """Test fallback from IndicTrans2 to NLLB when both Google and IndicTrans2 fail"""
    # Mock Google Translate failure
    translation_service.google_client = MagicMock()
    translation_service.google_client.translate.side_effect = Exception("Google API error")
    
    # Mock IndicTrans2 failure
    with patch.object(translation_service, '_translate_with_indic_trans2') as mock_indic:
        mock_indic.side_effect = Exception("IndicTrans2 error")
        
        # Mock NLLB success
        with patch.object(translation_service, '_translate_with_nllb') as mock_nllb:
            mock_nllb.return_value = TranslationResult(
                original_text="नमस्ते दुनिया",
                translated_text="Hello world",
                source_language="hi",
                target_language="en",
                confidence=0.7,
                method="nllb_200"
            )
            
            result = await translation_service.translate_text(
                "नमस्ते दुनिया", "hi", "en"
            )
            
            assert result.translated_text == "Hello world"
            assert result.method == "nllb_200"
            assert result.confidence == 0.7


@pytest.mark.asyncio
async def test_translate_text_all_methods_fail(translation_service):
    """Test when all translation methods fail"""
    # Mock Google Translate failure
    translation_service.google_client = MagicMock()
    translation_service.google_client.translate.side_effect = Exception("Google API error")
    
    # Mock IndicTrans2 failure
    with patch.object(translation_service, '_translate_with_indic_trans2') as mock_indic:
        mock_indic.side_effect = Exception("IndicTrans2 error")
        
        # Mock NLLB failure
        with patch.object(translation_service, '_translate_with_nllb') as mock_nllb:
            mock_nllb.side_effect = Exception("NLLB error")
            
            with pytest.raises(TranslationError) as exc_info:
                await translation_service.translate_text(
                    "नमस्ते दुनिया", "hi", "en"
                )
            
            assert "Translation failed" in str(exc_info.value)


@pytest.mark.asyncio
async def test_translate_with_indic_trans2_api(translation_service):
    """Test IndicTrans2 API translation for Indic to English"""
    with patch('requests.post') as mock_post:
        mock_response = MagicMock()
        mock_response.json.return_value = [{"translated_text": "Hello world"}]
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        result = await translation_service._translate_with_indic_trans2_api(
            "नमस्ते दुनिया", "hi", "en"
        )
        
        assert result.translated_text == "Hello world"
        assert result.method == "indic_trans2_api"
        assert result.confidence == 0.8


@pytest.mark.asyncio
async def test_translate_with_indic_trans2_local(translation_service):
    """Test IndicTrans2 local model translation for Indic to English"""
    # Mock tokenizer and model
    translation_service.indic_trans2_tokenizer = MagicMock()
    translation_service.indic_trans2_model = MagicMock()
    
    # Mock tokenizer output
    mock_inputs = {"input_ids": MagicMock(), "attention_mask": MagicMock()}
    translation_service.indic_trans2_tokenizer.return_value = mock_inputs
    
    # Mock model output
    mock_output = MagicMock()
    translation_service.indic_trans2_model.generate.return_value = [mock_output]
    translation_service.indic_trans2_tokenizer.decode.return_value = "Hello world"
    
    result = await translation_service._translate_with_indic_trans2_local(
        "नमस्ते दुनिया", "hi", "en"
    )
    
    assert result.translated_text == "Hello world"
    assert result.method == "indic_trans2_local"
    assert result.confidence == 0.8


@pytest.mark.asyncio
async def test_initialize_indic_trans2(translation_service):
    """Test IndicTrans2 model initialization for Indic to English translation"""
    with patch('transformers.AutoTokenizer.from_pretrained') as mock_tokenizer, \
         patch('transformers.AutoModelForSeq2SeqLM.from_pretrained') as mock_model:
        
        mock_tokenizer.return_value = MagicMock()
        mock_model.return_value = MagicMock()
        
        await translation_service._initialize_indic_trans2()
        
        assert translation_service._indic_trans2_initialized is True
        mock_tokenizer.assert_called_once_with("ai4bharat/indictrans2-indic-en-1B")
        mock_model.assert_called_once_with("ai4bharat/indictrans2-indic-en-1B")


@pytest.mark.asyncio
async def test_get_supported_languages(translation_service):
    """Test getting supported languages for all translation methods"""
    result = await translation_service.get_supported_languages()
    
    assert "google_translate" in result
    assert "indic_trans2" in result
    assert "nllb_200" in result
    
    # Check IndicTrans2 has additional languages
    indic_languages = [lang["code"] for lang in result["indic_trans2"]]
    assert "as" in indic_languages  # Assamese
    assert "ne" in indic_languages  # Nepali
    assert "ur" in indic_languages  # Urdu


@pytest.mark.asyncio
async def test_clean_text_for_translation(translation_service):
    """Test text cleaning for translation"""
    text = "  Hello   world  https://example.com  test@email.com  !!!  ???  "
    cleaned = translation_service._clean_text_for_translation(text)
    
    assert cleaned == "Hello world [URL] [EMAIL] ! ?"


@pytest.mark.asyncio
async def test_translation_caching(translation_service):
    """Test translation result caching"""
    # Mock cache service
    translation_service.cache_service.get.return_value = None
    translation_service.cache_service.set = AsyncMock()
    
    # Mock Google Translate success
    translation_service.google_client = MagicMock()
    translation_service.google_client.translate.return_value = {
        'translatedText': 'Hello world',
        'confidence': 0.95
    }
    
    result = await translation_service.translate_text(
        "नमस्ते दुनिया", "hi", "en"
    )
    
    # Verify cache was set
    translation_service.cache_service.set.assert_called_once()
    
    # Test cache hit
    translation_service.cache_service.get.return_value = result.json()
    
    cached_result = await translation_service.translate_text(
        "नमस्ते दुनिया", "hi", "en"
    )
    
    assert cached_result.translated_text == "Hello world"
