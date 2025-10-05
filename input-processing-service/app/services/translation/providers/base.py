"""
Base translation provider interface
"""

from abc import ABC, abstractmethod
from typing import Optional
from app.schemas.input_processing import TranslationResult


class TranslationProvider(ABC):
    """Base class for translation providers"""
    
    @abstractmethod
    async def translate(
        self, 
        text: str, 
        source_language: str, 
        target_language: str
    ) -> TranslationResult:
        """Translate text from source to target language"""
        pass
    
    @abstractmethod
    async def is_available(self) -> bool:
        """Check if this provider is available and configured"""
        pass
    
    @abstractmethod
    def get_provider_name(self) -> str:
        """Get the name of this provider"""
        pass
