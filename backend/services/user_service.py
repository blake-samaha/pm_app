"""User service for business logic."""
from typing import Optional
from sqlmodel import Session

from models import User, UserRole, AuthProvider
from repositories.user_repository import UserRepository
from exceptions import ResourceNotFoundError, DuplicateResourceError


class UserService:
    """Service layer for user-related business logic."""
    
    def __init__(self, session: Session):
        self.repository = UserRepository(session)
        self.session = session
    
    def get_user_by_id(self, user_id: str) -> User:
        """Get user by ID."""
        user = self.repository.get_by_id(user_id)
        if not user:
            raise ResourceNotFoundError(f"User with ID {user_id} not found")
        return user
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        return self.repository.get_by_email(email)
    
    def get_or_create_user(
        self, 
        email: str, 
        name: str, 
        auth_provider: AuthProvider
    ) -> tuple[User, bool]:
        """
        Get existing user or create new one.
        Returns tuple of (User, created: bool)
        """
        user = self.repository.get_by_email(email)
        if user:
            return user, False
        
        # Determine role based on email domain
        role = self._determine_role(email)
        
        user = self.repository.create_user(
            email=email,
            name=name,
            role=role,
            auth_provider=auth_provider
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

