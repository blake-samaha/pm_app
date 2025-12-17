"""Authentication router."""
import structlog
from fastapi import APIRouter, HTTPException, status

from schemas import GoogleLoginRequest, Token, UserRead
from dependencies import AuthServiceDep, CurrentUser

logger = structlog.get_logger()

router = APIRouter(
    prefix="/auth",
    tags=["authentication"],
)


@router.post("/login", response_model=Token)
async def login_with_firebase(
    request: GoogleLoginRequest,
    auth_service: AuthServiceDep
):
    """
    Login with Firebase ID token.
    Supports Google OAuth and Email/Password authentication.
    Creates user if doesn't exist.
    Returns JWT access token.
    """
    try:
        user, access_token = auth_service.authenticate_with_firebase(request.token)
        logger.info("User logged in successfully", user_id=str(user.id), email=user.email)
        return {"access_token": access_token, "token_type": "bearer"}
    except Exception as e:
        logger.error("Login failed", error=str(e), error_type=type(e).__name__)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )


@router.get("/me", response_model=UserRead)
async def get_current_user_info(current_user: CurrentUser):
    """Get current authenticated user information."""
    return current_user
