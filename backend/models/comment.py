"""Comment model."""

import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from models.action_item import ActionItem
    from models.risk import Risk
    from models.user import User


class Comment(SQLModel, table=True):
    """Comment model for action items and risks.

    A comment can be attached to either an ActionItem OR a Risk, but not both.
    Exactly one of action_item_id or risk_id should be set.
    """

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="user.id")
    content: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Parent references (one should be set, not both)
    action_item_id: Optional[uuid.UUID] = Field(
        default=None, foreign_key="actionitem.id"
    )
    risk_id: Optional[uuid.UUID] = Field(default=None, foreign_key="risk.id")

    # Relationships
    action_item: Optional["ActionItem"] = Relationship(back_populates="comments")
    risk: Optional["Risk"] = Relationship(back_populates="comments")
    user: "User" = Relationship(back_populates="comments")
