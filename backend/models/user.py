"""User model."""
from typing import List, TYPE_CHECKING
from sqlmodel import Field, SQLModel, Relationship
import uuid

from models import UserRole, AuthProvider
from models.links import UserProjectLink

if TYPE_CHECKING:
    from models.project import Project
    from models.comment import Comment


class User(SQLModel, table=True):
    """User model representing both Cogniters and Clients."""
    
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    email: str = Field(index=True, unique=True)
    name: str
    role: UserRole
    auth_provider: AuthProvider
    
    # Relationships
    projects: List["Project"] = Relationship(back_populates="users", link_model=UserProjectLink)
    comments: List["Comment"] = Relationship(back_populates="user")
