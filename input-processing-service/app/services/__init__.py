# Services package for Input Processing Service

# Maintain backward compatibility for renamed services
from .storage_facade import InputStorageService

__all__ = ["InputStorageService"]

