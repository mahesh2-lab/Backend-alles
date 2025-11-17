from __future__ import annotations
from typing import Optional, Dict, Any
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field, constr, HttpUrl

Filename = constr(strip_whitespace=True, min_length=1, max_length=255)


class FileBase(BaseModel):
    filename: Filename # type: ignore
    content_type: Optional[str] = None
    size: Optional[int] = Field(None, ge=0)
    metadata: Optional[Dict[str, Any]] = None


class FileCreate(FileBase):
    """
    Input schema when creating a file record.
    Note: actual binary payload handling (upload streams) should be done
    outside of this schema (e.g. FastAPI UploadFile).
    """
    owner_id: Optional[UUID] = None


class FileUpdate(BaseModel):
    filename: Optional[Filename] = None # type: ignore
    metadata: Optional[Dict[str, Any]] = None


class FileOut(FileBase):
    id: UUID
    owner_id: Optional[UUID] = None
    url: Optional[HttpUrl] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True