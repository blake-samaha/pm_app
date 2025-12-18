"""User schemas."""

import uuid
from typing import Optional

from pydantic import BaseModel

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
    is_pending: bool = False

    class Config:
        from_attributes = True


class InviteUserRequest(BaseModel):
    """Schema for inviting a user by email."""

    email: str


class InviteUserResponse(BaseModel):
    """Response after inviting/assigning a user."""

    user: UserRead
    was_created: bool  # True if a new placeholder user was created
    message: str


class UserUpdate(BaseModel):
    """Schema for updating user data."""

    name: Optional[str] = None


class UserRoleUpdate(BaseModel):
    """Schema for updating a user's role."""

    role: UserRole
