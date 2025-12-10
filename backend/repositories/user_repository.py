"""User repository."""
from typing import Optional
from sqlmodel import Session, select

from models import User, UserRole, AuthProvider
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
    
    def create_user(
        self, 
        email: str, 
        name: str, 
        role: UserRole, 
        auth_provider: AuthProvider
    ) -> User:
        """Create a new user."""
        user = User(
            email=email,
            name=name,
            role=role,
            auth_provider=auth_provider
        )
        return self.create(user)
    
    def email_exists(self, email: str) -> bool:
        """Check if email already exists."""
        return self.get_by_email(email) is not None

