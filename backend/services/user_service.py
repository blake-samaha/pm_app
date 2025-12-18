"""User service for business logic."""

from typing import List, Optional

from sqlmodel import Session

from exceptions import DuplicateResourceError, ResourceNotFoundError
from models import AuthProvider, User, UserRole
from repositories.user_repository import UserRepository


class UserService:
    """Service layer for user-related business logic."""

    def __init__(self, session: Session):
        self.repository = UserRepository(session)
        self.session = session

    def get_user_by_id(self, user_id: str) -> User:
        """Get user by ID."""
        from uuid import UUID

        # Convert string UUID to UUID object for database query
        uuid_obj = UUID(user_id) if isinstance(user_id, str) else user_id
        user = self.repository.get_by_id(uuid_obj)
        if not user:
            raise ResourceNotFoundError(f"User with ID {user_id} not found")
        return user

    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        return self.repository.get_by_email(email)

    def get_or_create_user(
        self, email: str, name: str, auth_provider: AuthProvider
    ) -> tuple[User, bool]:
        """
        Get existing user or create new one.
        If a pending user exists with this email, activate them.
        Returns tuple of (User, created: bool)
        """
        user = self.repository.get_by_email(email)
        if user:
            # If user is pending, activate them with the registration info
            if user.is_pending:
                user.name = name
                user.auth_provider = auth_provider
                user.is_pending = False
                self.session.add(user)
                self.session.commit()
                self.session.refresh(user)
                return (
                    user,
                    True,
                )  # Return True since this is effectively a new registration
            return user, False

        # Determine role based on email domain
        role = self._determine_role(email)

        user = self.repository.create_user(
            email=email, name=name, role=role, auth_provider=auth_provider
        )
        return user, True

    def _determine_role(self, email: str) -> UserRole:
        """Business rule: Determine user role based on email domain."""
        if email.endswith("@cognite.com"):
            return UserRole.COGNITER
        return UserRole.CLIENT

    def get_cogniters(self) -> list[User]:
        """Get all Cogniter users."""
        return self.repository.get_by_role(UserRole.COGNITER)

    def get_clients(self) -> list[User]:
        """Get all Client users."""
        return self.repository.get_by_role(UserRole.CLIENT)

    def search_users(
        self, search: Optional[str] = None, role: Optional[UserRole] = None
    ) -> List[User]:
        """
        Search users by name or email with optional role filtering.

        Args:
            search: Optional search string for name or email
            role: Optional role filter

        Returns:
            List of matching users
        """
        return self.repository.search(search=search, role=role)

    def create_pending_user(self, email: str) -> User:
        """
        Create a pending (placeholder) user that will be activated on registration.

        Args:
            email: The email address to invite

        Returns:
            The created pending user

        Raises:
            DuplicateResourceError: If email already exists
        """
        existing = self.repository.get_by_email(email)
        if existing:
            raise DuplicateResourceError(f"User with email {email} already exists")

        # Determine role based on email domain
        role = self._determine_role(email)

        # Create placeholder user with email as name (will be updated on registration)
        user = self.repository.create_pending_user(
            email=email,
            name=email.split("@")[0],  # Use email prefix as temporary name
            role=role,
        )
        return user

    def activate_pending_user(
        self, email: str, name: str, auth_provider: AuthProvider
    ) -> Optional[User]:
        """
        Activate a pending user when they register.

        Args:
            email: The email to look up
            name: The user's real name from registration
            auth_provider: The auth provider used to register

        Returns:
            The activated user if found and pending, None otherwise
        """
        user = self.repository.get_by_email(email)
        if user and user.is_pending:
            user.name = name
            user.auth_provider = auth_provider
            user.is_pending = False
            self.session.add(user)
            self.session.commit()
            self.session.refresh(user)
            return user
        return None

    def update_role(self, user_id, new_role: UserRole) -> User:
        """
        Update a user's role.

        Args:
            user_id: The user's ID (UUID or string)
            new_role: The new role to assign

        Returns:
            The updated user

        Raises:
            ResourceNotFoundError: If user not found
        """
        from uuid import UUID

        uuid_obj = UUID(str(user_id)) if not isinstance(user_id, UUID) else user_id
        user = self.repository.get_by_id(uuid_obj)
        if not user:
            raise ResourceNotFoundError(f"User with ID {user_id} not found")

        user.role = new_role
        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)
        return user
