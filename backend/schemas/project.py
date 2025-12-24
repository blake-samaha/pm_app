"""Project schemas.

Response schemas define field requiredness explicitly to ensure OpenAPI accurately
reflects the JSON response shape. Fields that are always present in responses are
marked as required (no default); fields that can be null are Optional without defaults.
"""

from datetime import date, datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from models.project import HealthStatus, ProjectBase, ProjectType, ReportingCycle


class ProjectCreate(ProjectBase):
    """Schema for creating a project. Inherits defaults from ProjectBase."""

    pass


class ProjectRead(BaseModel):
    """Schema for reading project data.

    All fields are explicitly defined to ensure OpenAPI required/nullable is accurate.
    - Required non-null fields: no default, not Optional
    - Required nullable fields: Optional[T] with no default (required in JSON but can be null)
    """

    model_config = ConfigDict(from_attributes=True)

    # Always present, never null
    id: UUID
    name: str
    precursive_url: str
    jira_url: str
    type: ProjectType
    reporting_cycle: ReportingCycle
    is_published: bool
    health_status: HealthStatus
    currency: str

    # Always present in JSON, but can be null
    client_logo_url: Optional[str]
    health_status_override: Optional[HealthStatus]
    precursive_id: Optional[str]
    jira_project_key: Optional[str]
    jira_project_name: Optional[str]
    jira_board_id: Optional[int]
    sprint_goals: Optional[str]
    last_synced_at: Optional[datetime]

    # Financial fields (can be null, or nulled by permission gating)
    total_budget: Optional[float]
    spent_budget: Optional[float]
    remaining_budget: Optional[float]
    overrun_investment: Optional[float]
    total_days_actuals: Optional[float]
    budgeted_days_delivery: Optional[float]
    budgeted_hours_delivery: Optional[float]

    # Date fields
    start_date: Optional[date]
    end_date: Optional[date]

    # Client info
    client_name: Optional[str]

    # Precursive health indicators
    precursive_project_health: Optional[str]
    precursive_time_health: Optional[str]
    precursive_cost_health: Optional[str]
    precursive_resources_health: Optional[str]
    precursive_status_summary: Optional[str]


class ProjectUpdate(BaseModel):
    """Schema for updating a project. All fields optional for PATCH semantics."""

    name: Optional[str] = None
    precursive_url: Optional[str] = None
    jira_url: Optional[str] = None
    client_logo_url: Optional[str] = None
    health_status_override: Optional[HealthStatus] = None
    is_published: Optional[bool] = None
    reporting_cycle: Optional[ReportingCycle] = None
    sprint_goals: Optional[str] = None
