from datetime import date, datetime
from enum import Enum
from typing import TYPE_CHECKING, List, Optional
from uuid import UUID, uuid4

from sqlmodel import Field, Relationship, SQLModel

from models.links import UserProjectLink

if TYPE_CHECKING:
    from models.action_item import ActionItem
    from models.risk import Risk
    from models.user import User


class ProjectType(str, Enum):
    FIXED_PRICE = "Fixed Price"
    TIME_AND_MATERIALS = "Time & Materials"
    RETAINER = "Retainer"


class ReportingCycle(str, Enum):
    WEEKLY = "Weekly"
    BIWEEKLY = "Bi-Weekly"
    MONTHLY = "Monthly"


class HealthStatus(str, Enum):
    GREEN = "Green"
    YELLOW = "Yellow"
    RED = "Red"


class ProjectBase(SQLModel):
    name: str = Field(index=True)
    precursive_url: Optional[str] = None
    jira_url: Optional[str] = None
    client_logo_url: Optional[str] = None
    type: ProjectType = Field(default=ProjectType.FIXED_PRICE)
    reporting_cycle: ReportingCycle = Field(default=ReportingCycle.WEEKLY)

    # Health Override
    health_status_override: Optional[HealthStatus] = None

    # Visibility
    is_published: bool = Field(default=False)

    # New fields for syncing
    precursive_id: Optional[str] = None
    jira_project_key: Optional[str] = None  # Extracted Jira Project Key (e.g. PROJ)
    jira_project_name: Optional[str] = None  # Fetched Jira Project Name
    jira_board_id: Optional[int] = None  # Extracted Jira board ID for sprint access

    # Sprint data (cached from Jira)
    sprint_goals: Optional[str] = None  # Active sprint goal from Jira

    # Financials (cached from Precursive)
    total_budget: Optional[float] = None
    spent_budget: Optional[float] = None
    remaining_budget: Optional[float] = None
    currency: str = Field(default="USD")

    # Dates
    start_date: Optional[date] = None
    end_date: Optional[date] = None

    client_name: Optional[str] = None


class Project(ProjectBase, table=True):
    id: Optional[UUID] = Field(default_factory=uuid4, primary_key=True)
    health_status: HealthStatus = Field(default=HealthStatus.GREEN)
    last_synced_at: Optional[datetime] = None

    # Relationships
    users: List["User"] = Relationship(
        back_populates="projects", link_model=UserProjectLink
    )
    actions: List["ActionItem"] = Relationship(back_populates="project")
    risks: List["Risk"] = Relationship(back_populates="project")
