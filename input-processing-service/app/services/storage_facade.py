"""
Storage facade to maintain compatibility when replacing the monolith InputStorageService
"""

import structlog
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
import redis.asyncio as aioredis

from app.core.config import settings
from app.core.exceptions import DatabaseError
from app.models.input_record import InputRecord
from app.models.processing_status import ProcessingStatus
from app.schemas.input_processing import (
    ProcessingStatusCreate,
    ProcessingStatusUpdate,
    ProcessingStatusResponse,
    ProcessingPhaseStatus,
    ProcessingPhase,
    ProcessingStatus as ProcessingStatusEnum
)
from app.repositories.input_repository import InputRepository
from app.repositories.status_repository import StatusRepository
from app.services.cache.cache_manager import CacheManager

logger = structlog.get_logger()


class InputStorageService:
    """Facade that maintains the original InputStorageService API while using new repository architecture"""
    
    def __init__(self, db: AsyncSession, redis: aioredis.Redis):
        self.db = db
        self.redis = redis
        
        # Initialize repositories and cache manager
        self.input_repo = InputRepository(db)
        self.status_repo = StatusRepository(db)
        self.cache_manager = CacheManager(redis)
    
    async def create_input_record(
        self,
        user_id: int,
        raw_input: str,
        session_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> InputRecord:
        """Create a new input record - maintains original API"""
        try:
            # Use repository for creation
            input_record = await self.input_repo.create(
                user_id=user_id,
                raw_input=raw_input,
                session_id=session_id,
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            # Cache the input record
            await self.cache_manager.cache_input_record(input_record.id, input_record)
            
            return input_record
            
        except Exception as e:
            logger.error("Failed to create input record", error=str(e))
            raise DatabaseError(f"Failed to create input record: {str(e)}")
    
    async def get_input_record(self, input_id: int) -> Optional[InputRecord]:
        """Get input record by ID - maintains original API"""
        try:
            # Try cache first
            cached_data = await self.cache_manager.get_cached_input_record(input_id)
            if cached_data:
                # Reconstruct InputRecord from cached data (simplified for compatibility)
                # In a full implementation, you'd want to handle this properly
                pass
            
            # Use repository for database lookup
            return await self.input_repo.get_by_id(input_id)
            
        except Exception as e:
            logger.error("Failed to get input record", input_id=input_id, error=str(e))
            raise DatabaseError(f"Failed to get input record: {str(e)}")
    
    async def update_input_record_status(
        self,
        input_id: int,
        status: str,
        current_phase: Optional[str] = None
    ) -> bool:
        """Update input record status - maintains original API"""
        try:
            # Use repository for update
            result = await self.input_repo.update_status(
                input_id=input_id,
                status=status,
                current_phase=current_phase
            )
            
            # Update cache if successful
            if result:
                await self.cache_manager.invalidate_input_record(input_id)
            
            return result
            
        except Exception as e:
            logger.error("Failed to update input record status", 
                        input_id=input_id, 
                        error=str(e))
            raise DatabaseError(f"Failed to update input record status: {str(e)}")
    
    async def create_processing_status(
        self,
        input_record_id: int,
        phase: ProcessingPhase,
        status: ProcessingStatusEnum,
        progress_percentage: int = 0,
        phase_data: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None,
        error_details: Optional[Dict[str, Any]] = None
    ) -> ProcessingStatus:
        """Create a new processing status record - maintains original API"""
        try:
            # Use repository for creation
            processing_status = await self.status_repo.create(
                input_record_id=input_record_id,
                phase=phase,
                status=status,
                progress_percentage=progress_percentage,
                phase_data=phase_data,
                error_message=error_message,
                error_details=error_details
            )
            
            # Cache the processing status
            await self.cache_manager.cache_processing_status(processing_status.id, processing_status)
            
            return processing_status
            
        except Exception as e:
            logger.error("Failed to create processing status", error=str(e))
            raise DatabaseError(f"Failed to create processing status: {str(e)}")
    
    async def update_processing_status(
        self,
        input_id: int,
        phase: ProcessingPhase,
        status: ProcessingStatusEnum,
        progress_percentage: int = 0,
        phase_data: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None,
        error_details: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Update processing status for a specific phase - maintains original API"""
        try:
            # Use repository for update
            result = await self.status_repo.update(
                input_id=input_id,
                phase=phase,
                status=status,
                progress_percentage=progress_percentage,
                phase_data=phase_data,
                error_message=error_message,
                error_details=error_details
            )
            
            # Update cache if successful
            if result:
                await self.cache_manager.invalidate_status_summary(input_id)
            
            return result
            
        except Exception as e:
            logger.error("Failed to update processing status", 
                        input_id=input_id, 
                        phase=phase.value, 
                        error=str(e))
            raise DatabaseError(f"Failed to update processing status: {str(e)}")
    
    async def get_processing_status(self, input_id: int) -> Optional[ProcessingStatusResponse]:
        """Get processing status for a specific input record - maintains original API"""
        try:
            # Try cache first
            cached_data = await self.cache_manager.get_cached_status_summary(input_id)
            if cached_data:
                return ProcessingStatusResponse(**cached_data)
            
            # Use repository for database lookup
            status_response = await self.status_repo.get_latest_status(input_id)
            
            if status_response:
                # Cache the result
                await self.cache_manager.cache_status_summary(
                    input_id, 
                    status_response.dict()
                )
            
            return status_response
            
        except Exception as e:
            logger.error("Failed to get processing status", input_id=input_id, error=str(e))
            raise DatabaseError(f"Failed to get processing status: {str(e)}")
    
    async def get_complete_processing_status(self, input_id: int) -> Optional[ProcessingStatusResponse]:
        """Get complete processing status with all phases - extends get_processing_status for detailed responses"""
        try:
            # Try cache first
            cached_data = await self.cache_manager.get_cached_status_summary(input_id)
            if cached_data and cached_data.get('phases'):
                return ProcessingStatusResponse(**cached_data)
            
            # Get all status records from repository
            all_statuses = await self.status_repo.get_all_statuses_for_input(input_id)
            
            if not all_statuses:
                return None
            
            # Build phases list from all records
            phases = []
            latest_status = all_statuses[-1]
            
            for status in all_statuses:
                phases.append(ProcessingPhaseStatus(
                    phase=status.phase,
                    status=status.status,
                    progress_percentage=status.progress_percentage,
                    started_at=status.started_at,
                    completed_at=status.completed_at,
                    duration_seconds=status.duration_seconds,
                    phase_data=status.phase_data if status.phase_data else None,
                    error_message=status.error_message,
                    error_details=status.error_details
                ))
            
            # Build complete response
            response = ProcessingStatusResponse(
                input_id=input_id,
                status=latest_status.status,
                current_phase=latest_status.phase,
                progress_percentage=latest_status.progress_percentage,
                phases=phases,
                created_at=all_statuses[0].created_at,
                updated_at=latest_status.created_at,
                processed_at=latest_status.completed_at
            )
            
            # Cache the complete result
            await self.cache_manager.cache_status_summary(input_id, response.dict())
            
            return response
            
        except Exception as e:
            logger.error("Failed to get complete processing status", input_id=input_id, error=str(e))
            raise DatabaseError(f"Failed to get complete processing status: {str(e)}")
    
    async def update_language_detection_results(
        self,
        input_id: int,
        detected_language: str,
        language_confidence: float
    ) -> bool:
        """Update language detection results - maintains original API"""
        try:
            result = await self.input_repo.update_language_detection(
                input_id=input_id,
                detected_language=detected_language,
                language_confidence=language_confidence
            )
            
            # Update cache if successful
            if result:
                await self.cache_manager.invalidate_input_record(input_id)
            
            return result
            
        except Exception as e:
            logger.error("Failed to update language detection results", 
                        input_id=input_id, 
                        error=str(e))
            raise DatabaseError(f"Failed to update language detection results: {str(e)}")
    
    async def update_translation_results(
        self,
        input_id: int,
        translation_result: dict
    ) -> bool:
        """Update translation results - maintains original API"""
        try:
            result = await self.input_repo.update_translation_result(
                input_id=input_id,
                translation_result=translation_result
            )
            
            # Update cache if successful
            if result:
                await self.cache_manager.invalidate_input_record(input_id)
            
            return result
            
        except Exception as e:
            logger.error("Failed to update translation results", 
                        input_id=input_id, 
                        error=str(e))
            raise DatabaseError(f"Failed to update translation results: {str(e)}")