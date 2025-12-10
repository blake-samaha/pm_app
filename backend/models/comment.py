"""Comment model."""
from typing import TYPE_CHECKING
from sqlmodel import Field, SQLModel, Relationship
from datetime import datetime, timezone
import uuid

if TYPE_CHECKING:
    from models.action_item import ActionItem
    from models.user import User


class Comment(SQLModel, table=True):
    """Comment model for action items."""
    
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    action_item_id: uuid.UUID = Field(foreign_key="actionitem.id")
    user_id: uuid.UUID = Field(foreign_key="user.id")
    content: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Relationships
    action_item: "ActionItem" = Relationship(back_populates="comments")
    user: "User" = Relationship(back_populates="comments")

