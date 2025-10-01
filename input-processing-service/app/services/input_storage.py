"""
Input storage service for database operations and caching
"""

import structlog
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload
import aioredis
from datetime import datetime

from app.core.config import settings
from app.core.exceptions import DatabaseError
from app.models.input_record import InputRecord
from app.models.processing_status import ProcessingStatus
from app.models.user import User
from app.schemas.input_processing import (
    InputRecordCreate,
    ProcessingStatusCreate,
    ProcessingStatusUpdate,
    ProcessingStatusResponse,
    ProcessingPhase,
    ProcessingStatus as ProcessingStatusEnum
)

logger = structlog.get_logger()


class InputStorageService:
    """Service for managing input records and processing status"""
    
    def __init__(self, db: AsyncSession, redis: aioredis.Redis):
        self.db = db
        self.redis = redis
    
    async def create_input_record(
        self,
        user_id: int,
        raw_input: str,
        session_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> InputRecord:
        """Create a new input record"""
        try:
            logger.info("Creating input record", user_id=user_id, input_length=len(raw_input))
            
            input_record = InputRecord(
                user_id=user_id,
                raw_input=raw_input,
                input_length=len(raw_input),
                session_id=session_id,
                ip_address=ip_address,
                user_agent=user_agent,
                status="pending",
                current_phase="validation"
            )
            
            self.db.add(input_record)
            await self.db.commit()
            await self.db.refresh(input_record)
            
            logger.info("Input record created", input_id=input_record.id)
            return input_record
            
        except Exception as e:
            await self.db.rollback()
            logger.error("Failed to create input record", error=str(e))
            raise DatabaseError(f"Failed to create input record: {str(e)}")
    
    async def get_input_record(self, input_id: int) -> Optional[InputRecord]:
        """Get input record by ID"""
        try:
            result = await self.db.execute(
                select(InputRecord)
                .options(selectinload(InputRecord.processing_statuses))
                .where(InputRecord.id == input_id)
            )
            return result.scalar_one_or_none()
            
        except Exception as e:
            logger.error("Failed to get input record", input_id=input_id, error=str(e))
            raise DatabaseError(f"Failed to get input record: {str(e)}")
    
    async def update_input_record_status(
        self,
        input_id: int,
        status: str,
        current_phase: Optional[str] = None
    ) -> bool:
        """Update input record status"""
        try:
            update_data = {"status": status, "updated_at": datetime.utcnow()}
            if current_phase:
                update_data["current_phase"] = current_phase
            if status == "completed":
                update_data["processed_at"] = datetime.utcnow()
            
            await self.db.execute(
                update(InputRecord)
                .where(InputRecord.id == input_id)
                .values(**update_data)
            )
            await self.db.commit()
            
            logger.info("Input record status updated", 
                       input_id=input_id, 
                       status=status, 
                       phase=current_phase)
            return True
            
        except Exception as e:
            await self.db.rollback()
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
                started_at=datetime.utcnow()
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
                    "progress_percentage": progress_percentage,
                    "updated_at": datetime.utcnow()
                }
                
                if phase_data:
                    update_data["phase_data"] = phase_data
                if error_message:
                    update_data["error_message"] = error_message
                if error_details:
                    update_data["error_details"] = error_details
                if status == ProcessingStatusEnum.COMPLETED:
                    update_data["completed_at"] = datetime.utcnow()
                    if processing_status.started_at:
                        duration = (datetime.utcnow() - processing_status.started_at).total_seconds()
                        update_data["duration_seconds"] = int(duration)
                
                await self.db.execute(
                    update(ProcessingStatus)
                    .where(ProcessingStatus.id == processing_status.id)
                    .values(**update_data)
                )
            else:
                # Create new record
                await self.create_processing_status(
                    input_id, phase, status, progress_percentage,
                    phase_data, error_message, error_details
                )
            
            await self.db.commit()
            
            logger.info("Processing status updated", 
                       input_id=input_id, 
                       phase=phase.value, 
                       status=status.value)
            return True
            
        except Exception as e:
            await self.db.rollback()
            logger.error("Failed to update processing status", 
                        input_id=input_id, 
                        error=str(e))
            raise DatabaseError(f"Failed to update processing status: {str(e)}")
    
    async def get_processing_status(self, input_id: int) -> Optional[ProcessingStatusResponse]:
        """Get complete processing status for an input record"""
        try:
            # Get input record with all processing statuses
            result = await self.db.execute(
                select(InputRecord)
                .options(selectinload(InputRecord.processing_statuses))
                .where(InputRecord.id == input_id)
            )
            input_record = result.scalar_one_or_none()
            
            if not input_record:
                return None
            
            # Convert to response format
            phases = []
            for status in input_record.processing_statuses:
                phases.append({
                    "phase": status.phase,
                    "status": status.status,
                    "progress_percentage": status.progress_percentage,
                    "started_at": status.started_at,
                    "completed_at": status.completed_at,
                    "duration_seconds": status.duration_seconds,
                    "phase_data": status.phase_data,
                    "error_message": status.error_message,
                    "error_details": status.error_details
                })
            
            return ProcessingStatusResponse(
                input_id=input_record.id,
                status=input_record.status,
                current_phase=input_record.current_phase,
                progress_percentage=self._calculate_overall_progress(phases),
                phases=phases,
                created_at=input_record.created_at,
                updated_at=input_record.updated_at,
                processed_at=input_record.processed_at
            )
            
        except Exception as e:
            logger.error("Failed to get processing status", 
                        input_id=input_id, 
                        error=str(e))
            raise DatabaseError(f"Failed to get processing status: {str(e)}")
    
    def _calculate_overall_progress(self, phases: list) -> int:
        """Calculate overall progress percentage from phases"""
        if not phases:
            return 0
        
        total_progress = sum(phase.get("progress_percentage", 0) for phase in phases)
        return min(100, total_progress // len(phases))
    
    async def get_user_input_records(
        self,
        user_id: int,
        limit: int = 50,
        offset: int = 0
    ) -> list[InputRecord]:
        """Get input records for a user"""
        try:
            result = await self.db.execute(
                select(InputRecord)
                .where(InputRecord.user_id == user_id)
                .order_by(InputRecord.created_at.desc())
                .limit(limit)
                .offset(offset)
            )
            return result.scalars().all()
            
        except Exception as e:
            logger.error("Failed to get user input records", 
                        user_id=user_id, 
                        error=str(e))
            raise DatabaseError(f"Failed to get user input records: {str(e)}")
    
    async def delete_input_record(self, input_id: int) -> bool:
        """Delete an input record and all related data"""
        try:
            # Delete processing statuses first
            await self.db.execute(
                ProcessingStatus.__table__.delete()
                .where(ProcessingStatus.input_record_id == input_id)
            )
            
            # Delete input record
            await self.db.execute(
                InputRecord.__table__.delete()
                .where(InputRecord.id == input_id)
            )
            
            await self.db.commit()
            
            logger.info("Input record deleted", input_id=input_id)
            return True
            
        except Exception as e:
            await self.db.rollback()
            logger.error("Failed to delete input record", 
                        input_id=input_id, 
                        error=str(e))
            raise DatabaseError(f"Failed to delete input record: {str(e)}")

