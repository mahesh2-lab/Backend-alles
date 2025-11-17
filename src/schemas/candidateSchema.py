from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import uuid


class CandidateBase(BaseModel):
    first_name: str
    last_name: str
    email: str
    phone: Optional[str] = None
    
class CandidateCreate(CandidateBase):
    id: Optional[uuid.UUID] = None
    skills: Optional[list[str]] = None
    experience: Optional[list[str]] = None
    experience_months: Optional[str] = None
    education: Optional[list[str]] = None

    evaluation_id: Optional[str] = None
    evaluated_by_id: Optional[str] = None

    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
        
class CandidateResponse(CandidateBase):
    id: uuid.UUID
    skills: Optional[list[str]] = None
    experience: Optional[list[str]] = None
    experience_months: Optional[str] = None
    education: Optional[list[str]] = None

    evaluation_id: Optional[str] = None
    evaluated_by_id: Optional[str] = None

    created_at: datetime
    updated_at: datetime
