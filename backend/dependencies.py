"""FastAPI dependencies for dependency injection and authorization."""

from typing import Annotated
from uuid import UUID

from fastapi import Depends, Header, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session

from config import Settings, get_settings
from database import get_session
from exceptions import AuthenticationError, ResourceNotFoundError
from models import User, UserRole
from services.action_service import ActionService
from services.auth_service import AuthService
from services.project_service import ProjectService
from services.risk_service import RiskService
from services.sync_job_service import SyncJobService
from services.sync_service import SyncService
from services.user_service import UserService

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


def get_risk_service(session: SessionDep) -> RiskService:
    """Get RiskService instance."""
    return RiskService(session)


def get_action_service(session: SessionDep) -> ActionService:
    """Get ActionService instance."""
    return ActionService(session)


def get_sync_job_service(session: SessionDep) -> SyncJobService:
    """Get SyncJobService instance."""
    return SyncJobService(session)


# Type aliases for common dependencies
UserServiceDep = Annotated[UserService, Depends(get_user_service)]
ProjectServiceDep = Annotated[ProjectService, Depends(get_project_service)]
AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]
SyncServiceDep = Annotated[SyncService, Depends(get_sync_service)]
RiskServiceDep = Annotated[RiskService, Depends(get_risk_service)]
ActionServiceDep = Annotated[ActionService, Depends(get_action_service)]
SyncJobServiceDep = Annotated[SyncJobService, Depends(get_sync_job_service)]


# Authentication dependencies
async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    auth_service: AuthServiceDep,
    user_service: UserServiceDep,
    x_impersonate_user_id: Annotated[str | None, Header()] = None,
) -> User:
    """
    Get current authenticated user from JWT token.

    If the user is a superuser and provides the X-Impersonate-User-Id header,
    returns the impersonated user instead for viewing the app from their perspective.
    """
    try:
        payload = auth_service.verify_token(token)
        user_id = payload.get("sub")
        is_superuser = payload.get("is_superuser", False)

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

    # Handle impersonation for superusers
    if is_superuser and x_impersonate_user_id:
        try:
            impersonated_user = user_service.get_user_by_id(x_impersonate_user_id)
            return impersonated_user
        except ResourceNotFoundError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot impersonate: User {x_impersonate_user_id} not found",
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
            detail="This action requires Cogniter role",
        )
    return current_user


async def require_project_access(
    project_id: UUID, current_user: CurrentUser, project_service: ProjectServiceDep
) -> User:
    """
    Require user to have access to specific project.
    Cogniters have access to all projects.
    Clients only have access to assigned projects.
    """
    if not project_service.user_has_access_to_project(project_id, current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this project",
        )
    return current_user


# Type aliases for authorization dependencies
CogniterUser = Annotated[User, Depends(require_cogniter)]


# ---------------------------------------------------------------------------
# Superuser-only dependencies (based on JWT claim, not DB role)
# ---------------------------------------------------------------------------


async def require_superuser(
    token: Annotated[str, Depends(oauth2_scheme)],
    auth_service: AuthServiceDep,
) -> dict:
    """
    Require the caller to be authenticated AND have the superuser JWT claim.

    This intentionally checks the *token payload* rather than the DB user role so that
    it remains valid even while the superuser is impersonating another user.
    """
    try:
        payload = auth_service.verify_token(token)
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not payload.get("is_superuser", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This action requires superuser access",
        )

    return payload


SuperuserPayload = Annotated[dict, Depends(require_superuser)]
