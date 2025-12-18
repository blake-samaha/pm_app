"""Users router."""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from dependencies import CogniterUser, UserServiceDep
from exceptions import ResourceNotFoundError
from models import UserRole
from schemas import UserRead

router = APIRouter(
    prefix="/users",
    tags=["users"],
)


@router.get("/", response_model=List[UserRead])
async def list_users(
    current_user: CogniterUser,  # Only Cogniters can list users
    user_service: UserServiceDep,
    search: Optional[str] = None,
    role: Optional[UserRole] = None,
):
    """
    List users with optional filtering.

    - **search**: Optional search string for name or email (case-insensitive)
    - **role**: Optional filter by role (Cogniter, Client + Financials, or Client)

    Only Cogniters can access this endpoint.
    """
    return user_service.search_users(search=search, role=role)


@router.patch("/{user_id}/role", response_model=UserRead)
async def update_user_role(
    user_id: UUID,
    new_role: UserRole,
    current_user: CogniterUser,  # Only Cogniters can update roles
    user_service: UserServiceDep,
):
    """
    Update a user's role.

    - Only Cogniters can update user roles
    - Cannot promote anyone to Cogniter role (security)
    - Can only change between CLIENT and CLIENT_FINANCIALS roles

    Use this to upgrade a client to Client + Financials for financial data access.
    """
    # Security: Cannot promote to Cogniter
    if new_role == UserRole.COGNITER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot promote users to Cogniter role",
        )

    try:
        return user_service.update_role(user_id, new_role)
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
