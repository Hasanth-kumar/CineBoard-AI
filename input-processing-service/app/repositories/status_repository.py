"""
Processing status repository for database operations
"""

import structlog
from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload 
from datetime import datetime, timezone

from app.core.exceptions import DatabaseError
from app.models.processing_status import ProcessingStatus
from app.schemas.input_processing import (
    ProcessingPhase,
    ProcessingStatus as ProcessingStatusEnum,
    ProcessingStatusResponse
)

logger = structlog.get_logger()


class StatusRepository:
    """Repository for ProcessingStatus CRUD operations"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create(
        self,
        input_record_id: int,
        phase: ProcessingPhase,
        status: ProcessingStatusEnum,
        progress_percentage: int = 0,
        phase_data: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None,
        error_details: Optional[Dict[str, Any]] = None
    ) -> ProcessingStatus:
        """Create a new processing status record"""
        try:
            processing_status = ProcessingStatus(
                input_record_id=input_record_id,
                phase=phase.value,
                status=status.value,
                progress_percentage=progress_percentage,
                phase_data=phase_data,
                error_message=error_message,
                error_details=error_details,
                started_at=datetime.now(timezone.utc)
            )
            
            self.db.add(processing_status)
            await self.db.commit()
            await self.db.refresh(processing_status)
            
            logger.info("Processing status created", 
                       status_id=processing_status.id, 
                       phase=phase.value, 
                       status=status.value)
            return processing_status
            
        except Exception as e:
            await self.db.rollback()
            logger.error("Failed to create processing status", error=str(e))
            raise DatabaseError(f"Failed to create processing status: {str(e)}")
    
    async def update(
        self,
        input_id: int,
        phase: ProcessingPhase,
        status: ProcessingStatusEnum,
        progress_percentage: int = 0,
        phase_data: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None,
        error_details: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Update processing status for a specific phase"""
        try:
            # Check if status record exists for this phase
            result = await self.db.execute(
                select(ProcessingStatus)
                .where(ProcessingStatus.input_record_id == input_id)
                .where(ProcessingStatus.phase == phase.value)
            )
            processing_status = result.scalar_one_or_none()
            
            if processing_status:
                # Update existing record
                update_data = {
                    "status": status.value,
                    "progress_percentage": progress_percentage
                }
                
                if phase_data:
                    update_data["phase_data"] = phase_data
                if error_message:
                    update_data["error_message"] = error_message
                if error_details:
                    update_data["error_details"] = error_details
                if status == ProcessingStatusEnum.COMPLETED:
                    update_data["completed_at"] = datetime.now(timezone.utc)
                    if processing_status.started_at:
                        duration = (datetime.now(timezone.utc) - processing_status.started_at).total_seconds()
                        update_data["duration_seconds"] = int(duration)
                
                await self.db.execute(
                    update(ProcessingStatus)
                    .where(ProcessingStatus.id == processing_status.id)
                    .values(**update_data)
                )
                await self.db.commit()
                
                logger.info("Processing status updated", 
                           input_id=input_id, 
                           phase=phase.value, 
                           status=status.value)
                return True
                
            else:
                # Create new record if it doesn't exist
                await self.create(
                    input_record_id=input_id,
                    phase=phase,
                    status=status,
                    progress_percentage=progress_percentage,
                    phase_data=phase_data,
                    error_message=error_message,
                    error_details=error_details
                )
                return True
                
        except Exception as e:
            await self.db.rollback()
            logger.error("Failed to update processing status", 
                        input_id=input_id, 
                        phase=phase.value, 
                        error=str(e))
            raise DatabaseError(f"Failed to update processing status: {str(e)}")
    
    async def get_latest_status(self, input_id: int) -> Optional[ProcessingStatusResponse]:
        """Get the latest processing status for an input record"""
        try:
            result = await self.db.execute(
                select(ProcessingStatus)
                .where(ProcessingStatus.input_record_id == input_id)
                .order_by(ProcessingStatus.created_at.desc())
                .limit(1)
            )
            status = result.scalar_one_or_none()
            
            if not status:
                return None
            
            return ProcessingStatusResponse(
                input_id=input_id,
                status=status.status,
                current_phase=status.phase,
                progress_percentage=status.progress_percentage,
                phase_data=status.phase_data,
                error_message=status.error_message,
                error_details=status.error_details,
                created_at=status.created_at,
                updated_at=status.created_at
            )
            
        except Exception as e:
            logger.error("Failed to get latest processing status", input_id=input_id, error=str(e))
            raise DatabaseError(f"Failed to get processing status: {str(e)}")
    
    async def get_all_statuses_for_input(self, input_id: int) -> List[ProcessingStatus]:
        """Get all processing statuses for an input record"""
        try:
            result = await self.db.execute(
                select(ProcessingStatus)
                .where(ProcessingStatus.input_record_id == input_id)
                .order_by(ProcessingStatus.created_at.asc())
            )
            return list(result.scalars().all())
            
        except Exception as e:
            logger.error("Failed to get processing statuses", input_id=input_id, error=str(e))
            raise DatabaseError(f"Failed to get processing statuses: {str(e)}")
    
    async def get_status_by_phase(
        self, 
        input_id: int, 
        phase: ProcessingPhase
    ) -> Optional[ProcessingStatus]:
        """Get processing status for a specific phase"""
        try:
            result = await self.db.execute(
                select(ProcessingStatus)
                .where(ProcessingStatus.input_record_id == input_id)
                .where(ProcessingStatus.phase == phase.value)
                .order_by(ProcessingStatus.created_at.desc())
                .limit(1)
            )
            return result.scalar_one_or_none()
            
        except Exception as e:
            logger.error("Failed to get status for phase", input_id=input_id, phase=phase.value, error=str(e))
            raise DatabaseError(f"Failed to get status for phase: {str(e)}")
    
    async def delete_for_input(self, input_id: int) -> bool:
        """Delete all processing statuses for an input record"""
        try:
            await self.db.execute(
                update(ProcessingStatus)
                .where(ProcessingStatus.input_record_id == input_id)
                .values(completed_at=datetime.now(timezone.utc))
            )
            await self.db.commit()
            
            logger.info("Processing statuses marked as completed for input", input_id=input_id)
            return True
            
        except Exception as e:
            await self.db.rollback()
            logger.error("Failed to delete processing statuses", input_id=input_id, error=str(e))
            raise DatabaseError(f"Failed to delete processing statuses: {str(e)}")
