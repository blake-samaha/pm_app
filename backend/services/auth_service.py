"""Authentication service for business logic."""

import os
from datetime import datetime, timedelta, timezone

import firebase_admin
from firebase_admin import auth as firebase_auth
from firebase_admin import credentials
from jose import jwt
from sqlmodel import Session

from config import Settings
from exceptions import AuthenticationError
from models import AuthProvider, User, UserRole
from services.user_service import UserService

# Initialize Firebase Admin SDK (only once)
_firebase_initialized = False


def initialize_firebase(settings: Settings):
    """Initialize Firebase Admin SDK."""
    global _firebase_initialized

    if _firebase_initialized:
        return

    try:
        # Check if already initialized
        firebase_admin.get_app()
        _firebase_initialized = True
        return
    except ValueError:
        pass

    # Initialize with service account if path provided AND file exists
    if settings.firebase_service_account_path and os.path.exists(
        settings.firebase_service_account_path
    ):
        cred = credentials.Certificate(settings.firebase_service_account_path)
        firebase_admin.initialize_app(cred)
    elif settings.firebase_project_id:
        # Initialize with just project ID (works with ADC or for token verification only)
        firebase_admin.initialize_app(
            options={"projectId": settings.firebase_project_id}
        )
    else:
        # No Firebase config available - skip initialization
        # This allows superuser login to work without Firebase
        return

    _firebase_initialized = True


class AuthService:
    """Service layer for authentication-related business logic."""

    def __init__(self, session: Session, settings: Settings):
        self.user_service = UserService(session)
        self.settings = settings
        self.session = session

        # Initialize Firebase
        initialize_firebase(settings)

    def authenticate_with_firebase(self, token: str) -> tuple[User, str]:
        """
        Authenticate user with Firebase ID token.
        Works for any Firebase auth provider (Google, Email/Password, etc.)
        Returns tuple of (User, access_token)
        """
        # Verify Firebase ID token
        firebase_user_data = self._verify_firebase_token(token)

        email = firebase_user_data.get("email")

        # Check for email BEFORE using it
        if not email:
            raise AuthenticationError("Email not found in Firebase token")

        # Now safe to use email for fallback name
        name = firebase_user_data.get("name") or email.split("@")[0]

        # Detect auth provider from Firebase token
        firebase_info = firebase_user_data.get("firebase", {})
        sign_in_provider = firebase_info.get("sign_in_provider", "password")

        if sign_in_provider == "google.com":
            auth_provider = AuthProvider.GOOGLE
        else:
            auth_provider = AuthProvider.EMAIL

        # Get or create user
        user, created = self.user_service.get_or_create_user(
            email=email, name=name, auth_provider=auth_provider
        )

        # Create access token
        access_token = self._create_access_token(user)

        return user, access_token

    def authenticate_superuser(self, email: str, password: str) -> tuple[User, str]:
        """
        Authenticate superuser with email/password (no Firebase).
        Creates the superuser if they don't exist.
        Returns tuple of (User, access_token)
        """
        # Hard safety guardrails
        if self.settings.environment == "production":
            raise AuthenticationError("Superuser login is disabled in production")

        # In non-development environments, require explicit enablement.
        if (
            self.settings.environment != "development"
            and not self.settings.allow_superuser_login
        ):
            raise AuthenticationError("Superuser login is disabled")

        # Check if superuser is configured
        if not self.settings.superuser_email or not self.settings.superuser_password:
            raise AuthenticationError("Superuser not configured")

        # Validate credentials against env vars
        if (
            email != self.settings.superuser_email
            or password != self.settings.superuser_password
        ):
            raise AuthenticationError("Invalid superuser credentials")

        # Get or create superuser with COGNITER role
        user, created = self.user_service.get_or_create_user(
            email=email,
            name="Superuser",
            auth_provider=AuthProvider.SUPERUSER,
        )

        # Ensure superuser always has COGNITER role
        if user.role != UserRole.COGNITER:
            user.role = UserRole.COGNITER
            self.session.add(user)
            self.session.commit()
            self.session.refresh(user)

        # Create access token with superuser flag
        access_token = self._create_access_token(user, is_superuser=True)

        return user, access_token

    def _verify_firebase_token(self, token: str) -> dict:
        """Verify Firebase ID token."""
        try:
            # Verify the ID token
            decoded_token = firebase_auth.verify_id_token(token)
            return decoded_token
        except firebase_auth.InvalidIdTokenError as e:
            raise AuthenticationError(f"Invalid Firebase token: {str(e)}")
        except firebase_auth.ExpiredIdTokenError as e:
            raise AuthenticationError(f"Expired Firebase token: {str(e)}")
        except firebase_auth.RevokedIdTokenError as e:
            raise AuthenticationError(f"Revoked Firebase token: {str(e)}")
        except Exception as e:
            raise AuthenticationError(f"Firebase token verification failed: {str(e)}")

    def _create_access_token(self, user: User, is_superuser: bool = False) -> str:
        """Create JWT access token for user."""
        expires_delta = timedelta(minutes=self.settings.access_token_expire_minutes)
        expire = datetime.now(timezone.utc) + expires_delta

        to_encode = {
            "sub": str(user.id),
            "role": user.role.value,
            "exp": expire,
            "is_superuser": is_superuser,
        }

        encoded_jwt = jwt.encode(
            to_encode, self.settings.secret_key, algorithm=self.settings.algorithm
        )
        return encoded_jwt

    def verify_token(self, token: str) -> dict:
        """Verify and decode JWT token."""
        try:
            payload = jwt.decode(
                token, self.settings.secret_key, algorithms=[self.settings.algorithm]
            )
            return payload
        except jwt.JWTError as e:
            raise AuthenticationError(f"Invalid token: {str(e)}")
