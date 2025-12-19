"""API serialization helpers (SQLModel -> Pydantic schemas).

Routers should own response shaping. Services should return SQLModel entities and
raw aggregates (counts) rather than Pydantic DTOs.
"""

from models import ActionItem, Comment, User
from schemas import ActionItemRead, CommentRead


def to_action_item_read(action: ActionItem, comment_count: int = 0) -> ActionItemRead:
    """Convert ActionItem SQLModel to ActionItemRead schema (injecting comment_count)."""
    model = ActionItemRead.model_validate(action)
    model.comment_count = comment_count
    return model


def to_comment_read(comment: Comment, author: User) -> CommentRead:
    """Convert Comment SQLModel to CommentRead schema (injecting author identity)."""
    model = CommentRead.model_validate(comment)
    model.author_name = author.name
    model.author_email = author.email
    return model
