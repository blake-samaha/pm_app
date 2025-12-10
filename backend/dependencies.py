"""FastAPI dependencies for dependency injection and authorization."""
from typing import Annotated
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session
from uuid import UUID

from database import get_session
from config import get_settings, Settings
from models import User, UserRole
from services.user_service import UserService
from services.project_service import ProjectService
from services.auth_service import AuthService
from services.sync_service import SyncService
from exceptions import AuthenticationError, AuthorizationError, ResourceNotFoundError

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


# Session dependency
SessionDep = Annotated[Session, Depends(get_session)]
SettingsDep = Annotated[Settings, Depends(get_settings)]


# Service dependencies
def get_user_service(session: SessionDep) -> UserService:
    """Get UserService instance."""
    return UserService(session)


def get_project_service(session: SessionDep) -> ProjectService:
    """Get ProjectService instance."""
    return ProjectService(session)


def get_auth_service(session: SessionDep, settings: SettingsDep) -> AuthService:
    """Get AuthService instance."""
    return AuthService(session, settings)


def get_sync_service(session: SessionDep, settings: SettingsDep) -> SyncService:
    """Get SyncService instance."""
    return SyncService(session, settings)


# Type aliases for common dependencies
UserServiceDep = Annotated[UserService, Depends(get_user_service)]
ProjectServiceDep = Annotated[ProjectService, Depends(get_project_service)]
AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]
SyncServiceDep = Annotated[SyncService, Depends(get_sync_service)]


# Authentication dependencies
async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    auth_service: AuthServiceDep,
    user_service: UserServiceDep
) -> User:
    """Get current authenticated user from JWT token."""
    try:
        payload = auth_service.verify_token(token)
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        user = user_service.get_user_by_id(user_id)
    except ResourceNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user


# Type alias for current user
CurrentUser = Annotated[User, Depends(get_current_user)]


# Authorization dependencies
async def require_cogniter(current_user: CurrentUser) -> User:
    """Require user to have Cogniter role."""
    if current_user.role != UserRole.COGNITER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This action requires Cogniter role"
        )
    return current_user


async def require_project_access(
    project_id: UUID,
    current_user: CurrentUser,
    project_service: ProjectServiceDep
) -> User:
    """
    Require user to have access to specific project.
    Cogniters have access to all projects.
    Clients only have access to assigned projects.
    """
    if not project_service.user_has_access_to_project(project_id, current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this project"
        )
    return current_user


# Type aliases for authorization dependencies
CogniterUser = Annotated[User, Depends(require_cogniter)]

