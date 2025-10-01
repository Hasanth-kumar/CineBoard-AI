"""
Text preprocessing service for cleaning, normalization, and formatting
"""

import re
import structlog
from typing import Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
import aioredis
import unicodedata

from app.core.config import settings
from app.schemas.input_processing import PreprocessingResult

logger = structlog.get_logger()


class TextPreprocessingService:
    """Service for preprocessing text before scene analysis"""
    
    def __init__(self, db: AsyncSession, redis: aioredis.Redis):
        self.db = db
        self.redis = redis
    
    async def preprocess_text(self, text: str) -> PreprocessingResult:
        """
        Preprocess text for better scene analysis
        """
        logger.info("Starting text preprocessing", text_length=len(text))
        
        original_text = text
        processed_text = text
        preprocessing_steps = []
        metadata = {}
        
        # Step 1: Normalize Unicode
        processed_text, unicode_info = self._normalize_unicode(processed_text)
        preprocessing_steps.append("unicode_normalization")
        metadata["unicode_info"] = unicode_info
        
        # Step 2: Clean whitespace
        processed_text, whitespace_info = self._clean_whitespace(processed_text)
        preprocessing_steps.append("whitespace_cleaning")
        metadata["whitespace_info"] = whitespace_info
        
        # Step 3: Remove special characters
        processed_text, special_chars_info = self._remove_special_characters(processed_text)
        preprocessing_steps.append("special_characters_removal")
        metadata["special_chars_info"] = special_chars_info
        
        # Step 4: Normalize punctuation
        processed_text, punctuation_info = self._normalize_punctuation(processed_text)
        preprocessing_steps.append("punctuation_normalization")
        metadata["punctuation_info"] = punctuation_info
        
        # Step 5: Fix common typos
        processed_text, typo_info = self._fix_common_typos(processed_text)
        preprocessing_steps.append("typo_correction")
        metadata["typo_info"] = typo_info
        
        # Step 6: Sentence segmentation
        processed_text, segmentation_info = self._segment_sentences(processed_text)
        preprocessing_steps.append("sentence_segmentation")
        metadata["segmentation_info"] = segmentation_info
        
        # Step 7: Final cleanup
        processed_text = self._final_cleanup(processed_text)
        preprocessing_steps.append("final_cleanup")
        
        result = PreprocessingResult(
            original_text=original_text,
            processed_text=processed_text,
            preprocessing_steps=preprocessing_steps,
            metadata=metadata
        )
        
        logger.info("Text preprocessing completed", 
                   original_length=len(original_text),
                   processed_length=len(processed_text),
                   steps_count=len(preprocessing_steps))
        
        return result
    
    def _normalize_unicode(self, text: str) -> tuple[str, Dict[str, Any]]:
        """Normalize Unicode characters"""
        original_length = len(text)
        
        # Normalize to NFC (Canonical Decomposition, followed by Canonical Composition)
        normalized_text = unicodedata.normalize('NFC', text)
        
        # Remove or replace problematic Unicode characters
        cleaned_text = ""
        removed_chars = []
        
        for char in normalized_text:
            if unicodedata.category(char) in ['Cc', 'Cf', 'Co', 'Cn']:
                # Control characters, format characters, private use, unassigned
                removed_chars.append(char)
            else:
                cleaned_text += char
        
        info = {
            "original_length": original_length,
            "normalized_length": len(cleaned_text),
            "removed_chars_count": len(removed_chars),
            "removed_chars": removed_chars[:10]  # Limit to first 10
        }
        
        return cleaned_text, info
    
    def _clean_whitespace(self, text: str) -> tuple[str, Dict[str, Any]]:
        """Clean and normalize whitespace"""
        original_length = len(text)
        
        # Replace multiple spaces with single space
        cleaned_text = re.sub(r' +', ' ', text)
        
        # Replace multiple newlines with single newline
        cleaned_text = re.sub(r'\n+', '\n', cleaned_text)
        
        # Replace tabs with spaces
        cleaned_text = cleaned_text.replace('\t', ' ')
        
        # Remove leading/trailing whitespace
        cleaned_text = cleaned_text.strip()
        
        info = {
            "original_length": original_length,
            "cleaned_length": len(cleaned_text),
            "spaces_normalized": True,
            "newlines_normalized": True
        }
        
        return cleaned_text, info
    
    def _remove_special_characters(self, text: str) -> tuple[str, Dict[str, Any]]:
        """Remove or replace special characters"""
        original_length = len(text)
        removed_chars = []
        
        # Keep only letters, numbers, spaces, and common punctuation
        allowed_pattern = r'[a-zA-Z0-9\s\.\,\!\?\;\:\-\(\)\[\]\{\}\"\'\/\\]'
        
        cleaned_text = ""
        for char in text:
            if re.match(allowed_pattern, char):
                cleaned_text += char
            else:
                removed_chars.append(char)
        
        info = {
            "original_length": original_length,
            "cleaned_length": len(cleaned_text),
            "removed_chars_count": len(removed_chars),
            "removed_chars": removed_chars[:10]  # Limit to first 10
        }
        
        return cleaned_text, info
    
    def _normalize_punctuation(self, text: str) -> tuple[str, Dict[str, Any]]:
        """Normalize punctuation marks"""
        original_length = len(text)
        
        # Replace multiple punctuation with single
        cleaned_text = re.sub(r'[!]{2,}', '!', text)
        cleaned_text = re.sub(r'[?]{2,}', '?', cleaned_text)
        cleaned_text = re.sub(r'[.]{2,}', '.', cleaned_text)
        cleaned_text = re.sub(r'[,]{2,}', ',', cleaned_text)
        
        # Normalize quotes
        cleaned_text = cleaned_text.replace('"', '"').replace('"', '"')
        cleaned_text = cleaned_text.replace("'", "'").replace("'", "'")
        
        # Normalize dashes
        cleaned_text = re.sub(r'[–—]', '-', cleaned_text)
        
        info = {
            "original_length": original_length,
            "normalized_length": len(cleaned_text),
            "punctuation_normalized": True
        }
        
        return cleaned_text, info
    
    def _fix_common_typos(self, text: str) -> tuple[str, Dict[str, Any]]:
        """Fix common typos and misspellings"""
        original_length = len(text)
        corrections_made = 0
        
        # Common typo patterns
        typo_patterns = {
            r'\bteh\b': 'the',
            r'\badn\b': 'and',
            r'\byuo\b': 'you',
            r'\bthier\b': 'their',
            r'\bthere\b': 'there',  # Context-dependent, simplified
            r'\bseperate\b': 'separate',
            r'\boccured\b': 'occurred',
            r'\brecieve\b': 'receive',
            r'\bacheive\b': 'achieve',
            r'\bdefinately\b': 'definitely'
        }
        
        cleaned_text = text
        for pattern, replacement in typo_patterns.items():
            if re.search(pattern, cleaned_text, re.IGNORECASE):
                cleaned_text = re.sub(pattern, replacement, cleaned_text, flags=re.IGNORECASE)
                corrections_made += 1
        
        info = {
            "original_length": original_length,
            "corrected_length": len(cleaned_text),
            "corrections_made": corrections_made
        }
        
        return cleaned_text, info
    
    def _segment_sentences(self, text: str) -> tuple[str, Dict[str, Any]]:
        """Segment text into sentences"""
        original_length = len(text)
        
        # Simple sentence segmentation
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        # Rejoin with proper spacing
        segmented_text = '. '.join(sentences)
        if segmented_text and not segmented_text.endswith('.'):
            segmented_text += '.'
        
        info = {
            "original_length": original_length,
            "segmented_length": len(segmented_text),
            "sentence_count": len(sentences),
            "sentences": sentences[:5]  # Limit to first 5 sentences
        }
        
        return segmented_text, info
    
    def _final_cleanup(self, text: str) -> str:
        """Final cleanup and validation"""
        # Remove extra spaces
        cleaned_text = ' '.join(text.split())
        
        # Ensure proper sentence ending
        if cleaned_text and not cleaned_text.endswith(('.', '!', '?')):
            cleaned_text += '.'
        
        return cleaned_text
    
    async def get_preprocessing_stats(self) -> Dict[str, Any]:
        """Get preprocessing statistics"""
        return {
            "preprocessing_steps": [
                "unicode_normalization",
                "whitespace_cleaning", 
                "special_characters_removal",
                "punctuation_normalization",
                "typo_correction",
                "sentence_segmentation",
                "final_cleanup"
            ],
            "supported_languages": settings.ALLOWED_LANGUAGES,
            "max_input_length": settings.MAX_INPUT_LENGTH,
            "min_input_length": settings.MIN_INPUT_LENGTH
        }

