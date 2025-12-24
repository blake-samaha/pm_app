"""User repository."""

from typing import List, Optional

from sqlmodel import Session, col, or_, select

from models import AuthProvider, User, UserRole
from repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    """Repository for User model with specialized queries."""

    def __init__(self, session: Session):
        super().__init__(User, session)

    def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email address."""
        statement = select(User).where(User.email == email)
        return self.session.exec(statement).first()

    def get_by_role(self, role: UserRole) -> list[User]:
        """Get all users with a specific role."""
        statement = select(User).where(User.role == role)
        return list(self.session.exec(statement).all())

    def search(
        self,
        search: Optional[str] = None,
        role: Optional[UserRole] = None,
        limit: int = 50,
    ) -> List[User]:
        """
        Search users by name or email with optional role filtering.

        Args:
            search: Optional search string for name or email (case-insensitive)
            role: Optional role filter
            limit: Maximum number of results to return (default 50)

        Returns:
            List of matching users (limited)
        """
        statement = select(User)

        if search:
            search_pattern = f"%{search}%"
            statement = statement.where(
                or_(
                    col(User.name).ilike(search_pattern),
                    col(User.email).ilike(search_pattern),
                )
            )

        if role:
            statement = statement.where(User.role == role)

        # Order by name for consistent results
        statement = statement.order_by(User.name)

        # Apply limit to prevent large payloads
        statement = statement.limit(limit)

        return list(self.session.exec(statement).all())

    def create_user(
        self, email: str, name: str, role: UserRole, auth_provider: AuthProvider
    ) -> User:
        """Create a new user."""
        user = User(
            email=email,
            name=name,
            role=role,
            auth_provider=auth_provider,
            is_pending=False,
        )
        return self.create(user)

    def create_pending_user(self, email: str, name: str, role: UserRole) -> User:
        """Create a pending (placeholder) user for invitation."""
        user = User(
            email=email,
            name=name,
            role=role,
            auth_provider=AuthProvider.EMAIL,  # Will be updated on registration
            is_pending=True,
        )
        return self.create(user)

    def email_exists(self, email: str) -> bool:
        """Check if email already exists."""
        return self.get_by_email(email) is not None
