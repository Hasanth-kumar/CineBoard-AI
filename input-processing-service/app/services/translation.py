"""
Translation service with Google Translate API → IndicTrans2 → NLLB-200 fallback chain
"""

import structlog
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
import aioredis
import google.cloud.translate_v2 as translate
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import torch
import requests
import json

from app.core.config import settings
from app.core.exceptions import TranslationError
from app.schemas.input_processing import TranslationResult
from app.core.redis import CacheService

logger = structlog.get_logger()


class TranslationService:
    """Service for translating text between languages"""
    
    def __init__(self, db: AsyncSession, redis: aioredis.Redis):
        self.db = db
        self.redis = redis
        self.cache_service = CacheService(redis)
        
        # Initialize Google Translate client
        self.google_client = None
        if settings.GOOGLE_TRANSLATE_API_KEY:
            try:
                self.google_client = translate.Client()
                logger.info("Google Translate client initialized")
            except Exception as e:
                logger.warning("Failed to initialize Google Translate client", error=str(e))
        
        # Initialize IndicTrans2 model (lazy loading)
        # IndicTrans2 is prioritized over NLLB for Indian languages due to:
        # 1. Better performance on Indic to English translation (Hindi, Telugu, Tamil, etc.)
        # 2. Superior cultural context understanding for Indian expressions
        # 3. Specialized training on Indian language to English corpora
        # 4. Better handling of regional idioms and colloquialisms
        self.indic_trans2_tokenizer = None
        self.indic_trans2_model = None
        self._indic_trans2_initialized = False
        
        # Initialize NLLB model (lazy loading) - fallback for non-Indian languages
        self.nllb_tokenizer = None
        self.nllb_model = None
        self._nllb_initialized = False
    
    async def translate_text(
        self, 
        text: str, 
        source_language: str, 
        target_language: str = None
    ) -> TranslationResult:
        """
        Translate text from source language to target language
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
        
        # Translation fallback chain: Google Translate → IndicTrans2 → NLLB-200
        
        # Step 1: Try Google Translate first (most reliable and fastest)
        if self.google_client:
            try:
                result = await self._translate_with_google(text, source_language, target_language)
                logger.info("Translation completed with Google Translate")
                
                # Cache the result
                await self.cache_service.set(
                    cache_key, 
                    result.json(), 
                    settings.CACHE_TTL_TRANSLATION
                )
                
                return result
            except Exception as e:
                logger.warning("Google Translate failed", error=str(e))
        
        # Step 2: Try IndicTrans2 as first fallback
        # IndicTrans2 is specifically designed for Indic to English translation and provides:
        # - Better accuracy for Hindi, Telugu, Tamil, Bengali, Gujarati to English
        # - Cultural context preservation for Indian expressions
        # - Superior handling of regional dialects and idioms
        try:
            result = await self._translate_with_indic_trans2(text, source_language, target_language)
            logger.info("Translation completed with IndicTrans2")
            
            # Cache the result
            await self.cache_service.set(
                cache_key, 
                result.json(), 
                settings.CACHE_TTL_TRANSLATION
            )
            
            return result
        except Exception as e:
            logger.warning("IndicTrans2 translation failed", error=str(e))
        
        # Step 3: Try NLLB-200 as final fallback
        # NLLB-200 is Meta's general-purpose multilingual model that:
        # - Supports 200+ languages including many low-resource languages
        # - Provides good baseline performance for non-Indian languages
        # - Serves as reliable fallback when specialized models fail
        try:
            result = await self._translate_with_nllb(text, source_language, target_language)
            logger.info("Translation completed with NLLB-200")
            
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
    
    async def _translate_with_google(
        self, 
        text: str, 
        source_language: str, 
        target_language: str
    ) -> TranslationResult:
        """Translate using Google Translate API"""
        try:
            result = self.google_client.translate(
                text, 
                target_language=target_language,
                source_language=source_language
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
    
    async def _translate_with_indic_trans2(
        self, 
        text: str, 
        source_language: str, 
        target_language: str
    ) -> TranslationResult:
        """Translate using IndicTrans2 model (AI4Bharat) - optimized for Indic to English translation"""
        try:
            # Initialize IndicTrans2 model if not already done
            if not self._indic_trans2_initialized:
                await self._initialize_indic_trans2()
            
            # Clean text
            cleaned_text = self._clean_text_for_translation(text)
            
            # Check if using HuggingFace Inference API or local model
            if settings.INDIC_TRANS2_ENDPOINT:
                # Use HuggingFace Inference API or self-hosted endpoint
                result = await self._translate_with_indic_trans2_api(
                    cleaned_text, source_language, target_language
                )
            else:
                # Use local model
                result = await self._translate_with_indic_trans2_local(
                    cleaned_text, source_language, target_language
                )
            
            return result
            
        except Exception as e:
            raise TranslationError(f"IndicTrans2 translation failed: {str(e)}")
    
    async def _translate_with_indic_trans2_api(
        self, 
        text: str, 
        source_language: str, 
        target_language: str
    ) -> TranslationResult:
        """Translate using IndicTrans2 via API endpoint"""
        try:
            # Prepare API request
            payload = {
                "inputs": text,
                "parameters": {
                    "src_lang": source_language,
                    "tgt_lang": target_language
                }
            }
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {settings.HUGGINGFACE_API_KEY}" if settings.HUGGINGFACE_API_KEY else None
            }
            
            # Remove None values from headers
            headers = {k: v for k, v in headers.items() if v is not None}
            
            response = requests.post(
                settings.INDIC_TRANS2_ENDPOINT,
                json=payload,
                headers=headers,
                timeout=30
            )
            response.raise_for_status()
            
            result_data = response.json()
            translated_text = result_data[0]["translated_text"] if isinstance(result_data, list) else result_data.get("translated_text", "")
            
            return TranslationResult(
                original_text=text,
                translated_text=translated_text,
                source_language=source_language,
                target_language=target_language,
                confidence=0.8,  # IndicTrans2 typically provides good quality for Indic to English translation
                method="indic_trans2_api"
            )
            
        except Exception as e:
            raise TranslationError(f"IndicTrans2 API translation failed: {str(e)}")
    
    async def _translate_with_indic_trans2_local(
        self, 
        text: str, 
        source_language: str, 
        target_language: str
    ) -> TranslationResult:
        """Translate using local IndicTrans2 model"""
        try:
            # Tokenize input
            inputs = self.indic_trans2_tokenizer(
                text, 
                return_tensors="pt", 
                padding=True, 
                truncation=True,
                max_length=512
            )
            
            # Generate translation
            with torch.no_grad():
                translated = self.indic_trans2_model.generate(
                    **inputs,
                    max_length=512,
                    num_beams=4,
                    early_stopping=True
                )
            
            # Decode translation
            translated_text = self.indic_trans2_tokenizer.decode(
                translated[0], 
                skip_special_tokens=True
            )
            
            return TranslationResult(
                original_text=text,
                translated_text=translated_text,
                source_language=source_language,
                target_language=target_language,
                confidence=0.8,  # IndicTrans2 typically provides good quality for Indic to English translation
                method="indic_trans2_local"
            )
            
        except Exception as e:
            raise TranslationError(f"IndicTrans2 local translation failed: {str(e)}")
    
    async def _initialize_indic_trans2(self):
        """Initialize IndicTrans2 model and tokenizer"""
        try:
            logger.info("Initializing IndicTrans2 model")
            
            # Use AI4Bharat's IndicTrans2 model
            # This model is specifically trained for Indic to English translation
            # and provides superior performance for Indian language to English pairs
            model_name = "ai4bharat/indictrans2-indic-en-1B"
            
            self.indic_trans2_tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.indic_trans2_model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
            
            # Set device
            device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            self.indic_trans2_model.to(device)
            
            self._indic_trans2_initialized = True
            logger.info("IndicTrans2 model initialized successfully")
            
        except Exception as e:
            logger.error("Failed to initialize IndicTrans2 model", error=str(e))
            raise TranslationError(f"IndicTrans2 initialization failed: {str(e)}")
    
    async def _translate_with_nllb(
        self, 
        text: str, 
        source_language: str, 
        target_language: str
    ) -> TranslationResult:
        """Translate using NLLB-200 model"""
        try:
            # Initialize NLLB model if not already done
            if not self._nllb_initialized:
                await self._initialize_nllb()
            
            # Clean text
            cleaned_text = self._clean_text_for_translation(text)
            
            # Tokenize input
            inputs = self.nllb_tokenizer(
                cleaned_text, 
                return_tensors="pt", 
                padding=True, 
                truncation=True,
                max_length=512
            )
            
            # Generate translation
            with torch.no_grad():
                translated = self.nllb_model.generate(
                    **inputs,
                    max_length=512,
                    num_beams=4,
                    early_stopping=True
                )
            
            # Decode translation
            translated_text = self.nllb_tokenizer.decode(
                translated[0], 
                skip_special_tokens=True
            )
            
            return TranslationResult(
                original_text=text,
                translated_text=translated_text,
                source_language=source_language,
                target_language=target_language,
                confidence=0.7,  # NLLB doesn't provide confidence scores
                method="nllb_200"
            )
            
        except Exception as e:
            raise TranslationError(f"NLLB-200 translation failed: {str(e)}")
    
    async def _initialize_nllb(self):
        """Initialize NLLB-200 model and tokenizer"""
        try:
            logger.info("Initializing NLLB-200 model")
            
            model_name = "facebook/nllb-200-distilled-600M"
            
            self.nllb_tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.nllb_model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
            
            # Set device
            device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            self.nllb_model.to(device)
            
            self._nllb_initialized = True
            logger.info("NLLB-200 model initialized successfully")
            
        except Exception as e:
            logger.error("Failed to initialize NLLB-200 model", error=str(e))
            raise TranslationError(f"NLLB-200 initialization failed: {str(e)}")
    
    def _clean_text_for_translation(self, text: str) -> str:
        """Clean text for better translation"""
        # Remove extra whitespace
        cleaned = ' '.join(text.split())
        
        # Remove URLs and email addresses
        import re
        cleaned = re.sub(r'https?://[^\s]+', '[URL]', cleaned)
        cleaned = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL]', cleaned)
        
        # Remove excessive punctuation
        cleaned = re.sub(r'[!]{3,}', '!', cleaned)
        cleaned = re.sub(r'[?]{3,}', '?', cleaned)
        
        return cleaned.strip()
    
    async def get_supported_languages(self) -> Dict[str, Any]:
        """Get list of supported languages for translation"""
        return {
            "google_translate": [
                {"code": "en", "name": "English"},
                {"code": "hi", "name": "Hindi"},
                {"code": "te", "name": "Telugu"},
                {"code": "ta", "name": "Tamil"},
                {"code": "bn", "name": "Bengali"},
                {"code": "gu", "name": "Gujarati"},
                {"code": "mr", "name": "Marathi"},
                {"code": "kn", "name": "Kannada"},
                {"code": "ml", "name": "Malayalam"},
                {"code": "or", "name": "Odia"},
                {"code": "pa", "name": "Punjabi"}
            ],
            "indic_trans2": [
                {"code": "en", "name": "English"},
                {"code": "hi", "name": "Hindi"},
                {"code": "te", "name": "Telugu"},
                {"code": "ta", "name": "Tamil"},
                {"code": "bn", "name": "Bengali"},
                {"code": "gu", "name": "Gujarati"},
                {"code": "mr", "name": "Marathi"},
                {"code": "kn", "name": "Kannada"},
                {"code": "ml", "name": "Malayalam"},
                {"code": "or", "name": "Odia"},
                {"code": "pa", "name": "Punjabi"},
                {"code": "as", "name": "Assamese"},
                {"code": "ne", "name": "Nepali"},
                {"code": "ur", "name": "Urdu"}
            ],
            "nllb_200": [
                {"code": "en", "name": "English"},
                {"code": "hi", "name": "Hindi"},
                {"code": "te", "name": "Telugu"},
                {"code": "ta", "name": "Tamil"},
                {"code": "bn", "name": "Bengali"},
                {"code": "gu", "name": "Gujarati"},
                {"code": "mr", "name": "Marathi"},
                {"code": "kn", "name": "Kannada"},
                {"code": "ml", "name": "Malayalam"},
                {"code": "or", "name": "Odia"},
                {"code": "pa", "name": "Punjabi"}
            ]
        }

