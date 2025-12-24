"""API serialization helpers (SQLModel -> Pydantic schemas).

Routers should own response shaping. Services should return SQLModel entities and
raw aggregates (counts) rather than Pydantic DTOs.
"""

from models import ActionItem, Comment, User
from schemas import ActionItemRead, CommentRead


def to_action_item_read(action: ActionItem, comment_count: int = 0) -> ActionItemRead:
    """Convert ActionItem SQLModel to ActionItemRead schema (injecting comment_count)."""
    # Build a dict from the model and add the enriched field
    data = {
        "id": action.id,
        "project_id": action.project_id,
        "title": action.title,
        "status": action.status,
        "priority": action.priority,
        "comment_count": comment_count,
        "assignee": action.assignee,
        "due_date": action.due_date,
        "jira_id": action.jira_id,
        "jira_key": action.jira_key,
        "issue_type": action.issue_type,
        "last_synced_at": action.last_synced_at,
    }
    return ActionItemRead.model_validate(data)


def to_comment_read(comment: Comment, author: User) -> CommentRead:
    """Convert Comment SQLModel to CommentRead schema (injecting author identity)."""
    # Build a dict from the model and add the enriched fields
    data = {
        "id": comment.id,
        "user_id": comment.user_id,
        "content": comment.content,
        "created_at": comment.created_at,
        "action_item_id": comment.action_item_id,
        "risk_id": comment.risk_id,
        "author_name": author.name,
        "author_email": author.email,
    }
    return CommentRead.model_validate(data)
