from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel

from models.project import HealthStatus, ProjectBase, ReportingCycle


class ProjectCreate(ProjectBase):
    pass


class ProjectRead(ProjectBase):
    id: UUID
    health_status: HealthStatus
    last_synced_at: Optional[datetime] = None
    jira_project_key: Optional[str] = None
    jira_project_name: Optional[str] = None
    jira_board_id: Optional[int] = None
    sprint_goals: Optional[str] = None


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    precursive_url: Optional[str] = None
    jira_url: Optional[str] = None
    client_logo_url: Optional[str] = None
    health_status_override: Optional[HealthStatus] = None
    is_published: Optional[bool] = None
    reporting_cycle: Optional[ReportingCycle] = None
    sprint_goals: Optional[str] = None
