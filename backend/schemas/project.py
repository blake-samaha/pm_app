"""Project schemas."""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import uuid
from models import ProjectType, ReportingCycle, HealthStatus


class ProjectBase(BaseModel):
    """Base project schema."""
    name: str
    precursive_url: str
    jira_url: str
    client_logo_url: Optional[str] = None
    type: ProjectType
    reporting_cycle: Optional[ReportingCycle] = None
    health_status: HealthStatus = HealthStatus.GREEN
    health_status_override: Optional[HealthStatus] = None
    is_published: bool = False


class ProjectCreate(BaseModel):
    """Schema for creating a project."""
    name: str
    precursive_url: str
    jira_url: str
    client_logo_url: Optional[str] = None
    type: ProjectType
    reporting_cycle: Optional[ReportingCycle] = None


class ProjectRead(ProjectBase):
    """Schema for reading project data."""
    id: uuid.UUID
    
    # Sync metadata
    last_synced_at: Optional[datetime] = None
    precursive_id: Optional[str] = None
    
    # Financial data (from Precursive)
    total_budget: Optional[float] = None
    spent_budget: Optional[float] = None
    remaining_budget: Optional[float] = None
    currency: str = "USD"
    
    # Project dates (from Precursive)
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    client_name: Optional[str] = None
    
    class Config:
        from_attributes = True


class ProjectUpdate(BaseModel):
    """Schema for updating project data."""
    name: Optional[str] = None
    jira_url: Optional[str] = None
    client_logo_url: Optional[str] = None
    reporting_cycle: Optional[ReportingCycle] = None
    health_status_override: Optional[HealthStatus] = None
    is_published: Optional[bool] = None
