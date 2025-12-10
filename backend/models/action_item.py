"""Action Item model."""
from typing import List, Optional, TYPE_CHECKING
from sqlmodel import Field, SQLModel, Relationship
from datetime import datetime
import uuid

from models import ActionStatus, Priority

if TYPE_CHECKING:
    from models.project import Project
    from models.comment import Comment


class ActionItem(SQLModel, table=True):
    """Action Item model for project tasks and actions."""
    
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    project_id: uuid.UUID = Field(foreign_key="project.id")
    title: str
    status: ActionStatus = Field(default=ActionStatus.TO_DO)
    assignee: Optional[str] = None 
    due_date: Optional[datetime] = None
    priority: Priority = Field(default=Priority.MEDIUM)
    
    # Jira integration fields
    jira_id: Optional[str] = None  # Internal Jira issue ID
    jira_key: Optional[str] = Field(default=None, index=True)  # e.g., "PROJ-123"
    issue_type: Optional[str] = None  # Bug, Story, Task, Epic
    
    # Sync tracking
    last_synced_at: Optional[datetime] = None
    
    # Relationships
    project: "Project" = Relationship(back_populates="actions")
    comments: List["Comment"] = Relationship(back_populates="action_item")
