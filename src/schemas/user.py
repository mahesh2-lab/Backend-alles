from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional
import uuid


class UserBase(BaseModel):
    email: EmailStr
    name: str = Field(...)
    team_role: str = Field(...)
    username: str = Field(..., min_length=3, max_length=50)


class UserCreate(UserBase):
    password: str = Field(..., max_length=100)


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    team_role: Optional[str] = None


class UserInDB(UserBase):
    id: uuid.UUID
    team_role: str
    created_at: datetime
    updated_at: datetime

    # pydantic v2 config
    model_config = {"from_attributes": True}


class UserResponse(UserInDB):
    pass
