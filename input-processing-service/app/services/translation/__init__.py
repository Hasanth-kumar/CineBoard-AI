# Maintain backward compatibility - export facade as TranslationService
from .translation_facade import TranslationServiceFacade as TranslationService

__all__ = ["TranslationService"]
