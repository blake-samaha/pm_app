"""Project model."""
from typing import List, Optional, TYPE_CHECKING
from sqlmodel import Field, SQLModel, Relationship
from datetime import datetime
import uuid

from models import ProjectType, ReportingCycle, HealthStatus
from models.links import UserProjectLink

if TYPE_CHECKING:
    from models.user import User
    from models.action_item import ActionItem
    from models.risk import Risk


class Project(SQLModel, table=True):
    """Project model."""
    
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str
    precursive_url: str = Field(unique=True)
    jira_url: str
    client_logo_url: Optional[str] = None
    type: ProjectType
    reporting_cycle: Optional[ReportingCycle] = None
    health_status: HealthStatus = Field(default=HealthStatus.GREEN)
    health_status_override: Optional[HealthStatus] = None
    is_published: bool = Field(default=False)
    
    # Sync tracking
    last_synced_at: Optional[datetime] = None
    precursive_id: Optional[str] = None  # Salesforce record ID (18 char)
    
    # Financial data (from Precursive)
    total_budget: Optional[float] = None
    spent_budget: Optional[float] = None
    remaining_budget: Optional[float] = None
    currency: str = Field(default="USD")
    
    # Project dates (from Precursive)
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    client_name: Optional[str] = None
    
    # Relationships
    users: List["User"] = Relationship(back_populates="projects", link_model=UserProjectLink)
    actions: List["ActionItem"] = Relationship(back_populates="project")
    risks: List["Risk"] = Relationship(back_populates="project")
