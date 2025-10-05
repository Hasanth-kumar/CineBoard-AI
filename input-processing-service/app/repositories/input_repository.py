"""
Input record repository for database operations
"""

import structlog
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload
from datetime import datetime

from app.core.exceptions import DatabaseError
from app.models.input_record import InputRecord

logger = structlog.get_logger()


class InputRepository:
    """Repository for InputRecord CRUD operations"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create(
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
    
    async def get_by_id(self, input_id: int) -> Optional[InputRecord]:
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
    
    async def update_status(
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
    
    async def get_by_user_id(
        self, 
        user_id: int, 
        limit: int = 50, 
        offset: int = 0
    ) -> List[InputRecord]:
        """Get input records for a user"""
        try:
            result = await self.db.execute(
                select(InputRecord)
                .where(InputRecord.user_id == user_id)
                .order_by(InputRecord.created_at.desc())
                .limit(limit)
                .offset(offset)
            )
            return list(result.scalars().all())
            
        except Exception as e:
            logger.error("Failed to get input records for user", user_id=user_id, error=str(e))
            raise DatabaseError(f"Failed to get input records: {str(e)}")
    
    async def get_by_session_id(
        self, 
        session_id: str, 
        limit: int = 50, 
        offset: int = 0
    ) -> List[InputRecord]:
        """Get input records for a session"""
        try:
            result = await self.db.execute(
                select(InputRecord)
                .where(InputRecord.session_id == session_id)
                .order_by(InputRecord.created_at.desc())
                .limit(limit)
                .offset(offset)
            )
            return list(result.scalars().all())
            
        except Exception as e:
            logger.error("Failed to get input records for session", session_id=session_id, error=str(e))
            raise DatabaseError(f"Failed to get input records: {str(e)}")
    
    async def update_language_detection(
        self,
        input_id: int,
        detected_language: str,
        language_confidence: float
    ) -> bool:
        """Update language detection results in input record"""
        try:
            await self.db.execute(
                update(InputRecord)
                .where(InputRecord.id == input_id)
                .values(
                    detected_language=detected_language,
                    language_confidence=str(language_confidence),
                    updated_at=datetime.utcnow()
                )
            )
            await self.db.commit()
            
            logger.info("Language detection results updated", 
                       input_id=input_id, 
                       language=detected_language,
                       confidence=language_confidence)
            return True
            
        except Exception as e:
            await self.db.rollback()
            logger.error("Failed to update language detection", 
                        input_id=input_id, 
                        error=str(e))
            raise DatabaseError(f"Failed to update language detection: {str(e)}")
    
    async def update_translation_result(
        self,
        input_id: int,
        translation_result: dict
    ) -> bool:
        """Update translation result in input record"""
        try:
            await self.db.execute(
                update(InputRecord)
                .where(InputRecord.id == input_id)
                .values(
                    translation_result=translation_result,
                    updated_at=datetime.utcnow()
                )
            )
            await self.db.commit()
            
            logger.info("Translation result updated", 
                       input_id=input_id)
            return True
            
        except Exception as e:
            await self.db.rollback()
            logger.error("Failed to update translation result", 
                        input_id=input_id, 
                        error=str(e))
            raise DatabaseError(f"Failed to update translation result: {str(e)}")
    
    async def delete(self, input_id: int) -> bool:
        """Delete an input record"""
        try:
            result = await self.db.execute(
                select(InputRecord).where(InputRecord.id == input_id)
            )
            input_record = result.scalar_one_or_none()
            
            if not input_record:
                return False
            
            await self.db.delete(input_record)
            await self.db.commit()
            
            logger.info("Input record deleted", input_id=input_id)
            return True
            
        except Exception as e:
            await self.db.rollback()
            logger.error("Failed to delete input record", input_id=input_id, error=str(e))
            raise DatabaseError(f"Failed to delete input record: {str(e)}")
