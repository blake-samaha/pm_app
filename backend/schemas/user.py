"""User schemas."""
from pydantic import BaseModel
from typing import Optional
import uuid
from models import UserRole


class UserBase(BaseModel):
    """Base user schema."""
    email: str
    name: str


class UserCreate(UserBase):
    """Schema for creating a user."""
    pass


class UserRead(BaseModel):
    """Schema for reading user data."""
    id: uuid.UUID
    email: str
    name: str
    role: UserRole
    
    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    """Schema for updating user data."""
    name: Optional[str] = None
