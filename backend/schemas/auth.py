"""Authentication schemas."""

from pydantic import BaseModel


class GoogleLoginRequest(BaseModel):
    """Request schema for Google login."""

    token: str


class SuperuserLoginRequest(BaseModel):
    """Request schema for superuser login (bypasses Firebase)."""

    email: str
    password: str


class Token(BaseModel):
    """JWT token response schema."""

    access_token: str
    token_type: str
    is_superuser: bool = False
