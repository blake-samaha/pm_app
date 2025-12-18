"""Authentication router."""

from typing import List

import structlog
from fastapi import APIRouter, HTTPException, status

from dependencies import AuthServiceDep, CurrentUser, SuperuserPayload, UserServiceDep
from schemas import GoogleLoginRequest, SuperuserLoginRequest, Token, UserRead

logger = structlog.get_logger()

router = APIRouter(
    prefix="/auth",
    tags=["authentication"],
)


@router.post("/login", response_model=Token)
async def login_with_firebase(
    request: GoogleLoginRequest, auth_service: AuthServiceDep
):
    """
    Login with Firebase ID token.
    Supports Google OAuth and Email/Password authentication.
    Creates user if doesn't exist.
    Returns JWT access token.
    """
    try:
        user, access_token = auth_service.authenticate_with_firebase(request.token)
        logger.info(
            "User logged in successfully", user_id=str(user.id), email=user.email
        )
        return {"access_token": access_token, "token_type": "bearer"}
    except Exception as e:
        logger.error("Login failed", error=str(e), error_type=type(e).__name__)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


@router.post("/superuser-login", response_model=Token)
async def login_superuser(request: SuperuserLoginRequest, auth_service: AuthServiceDep):
    """
    Login as superuser with email/password (bypasses Firebase).
    Only works if SUPERUSER_EMAIL and SUPERUSER_PASSWORD are configured.
    """
    try:
        user, access_token = auth_service.authenticate_superuser(
            request.email, request.password
        )
        logger.info("Superuser logged in", user_id=str(user.id))
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "is_superuser": True,
        }
    except Exception as e:
        logger.error("Superuser login failed", error=str(e))
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


@router.get("/me", response_model=UserRead)
async def get_current_user_info(current_user: CurrentUser):
    """Get current authenticated user information."""
    return current_user


@router.get("/impersonation-presets", response_model=List[UserRead])
async def get_impersonation_presets(
    _: SuperuserPayload,
    user_service: UserServiceDep,
):
    """
    Return stable QA personas for superuser impersonation.

    This endpoint is superuser-only (checked via JWT claim), and is safe to call even
    while the superuser is impersonating another user.
    """
    return user_service.ensure_qa_personas()
