"""Users router."""
from fastapi import APIRouter
from typing import List, Optional

from schemas import UserRead
from models import UserRole
from dependencies import CogniterUser, UserServiceDep

router = APIRouter(
    prefix="/users",
    tags=["users"],
)


@router.get("/", response_model=List[UserRead])
async def list_users(
    current_user: CogniterUser,  # Only Cogniters can list users
    user_service: UserServiceDep,
    search: Optional[str] = None,
    role: Optional[UserRole] = None
):
    """
    List users with optional filtering.
    
    - **search**: Optional search string for name or email (case-insensitive)
    - **role**: Optional filter by role (Cogniter or Client)
    
    Only Cogniters can access this endpoint.
    """
    return user_service.search_users(search=search, role=role)

