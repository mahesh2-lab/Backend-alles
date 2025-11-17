from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import uuid


class RequisitionCreate(BaseModel):
    requisition: str
    description: Optional[str] = None


class RequisitionUpdate(BaseModel):
    requisition: Optional[str] = None
    description: Optional[str] = None


class RequisitionResponse(BaseModel):
    id: uuid.UUID
    requisition: str
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    # pydantic v2: allow building model from ORM objects
    model_config = {"from_attributes": True}


class RequisitionCreateResponse(BaseModel):
    success: bool
    requisition: RequisitionResponse

    model_config = {"from_attributes": True}

class ListRequisitionsResponse(BaseModel):
    success: bool
    requisitions: list[RequisitionResponse]

    model_config = {"from_attributes": True}