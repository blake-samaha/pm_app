from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from models import SyncJobStatus, SyncJobType


class JiraSyncResult(BaseModel):
    success: bool
    actions_count: int = 0
    message: Optional[str] = None
    error: Optional[str] = None


class PrecursiveSyncResult(BaseModel):
    success: bool
    financials_updated: bool = False
    risks_count: int = 0
    message: Optional[str] = None
    error: Optional[str] = None


class SyncResult(BaseModel):
    project_id: UUID
    timestamp: datetime
    jira: JiraSyncResult
    precursive: PrecursiveSyncResult


# ============================================================================
# Sync Job Schemas (for 202 async pattern)
# ============================================================================


class SyncJobSummary(BaseModel):
    """Compact sync job summary for status card UI."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    job_type: SyncJobType
    status: SyncJobStatus
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    items_synced: int = 0
    error: Optional[str] = None


class SyncJobRead(BaseModel):
    """Schema for reading sync job data."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: UUID
    job_type: SyncJobType
    status: SyncJobStatus
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    requested_by_user_id: Optional[UUID] = None
    error: Optional[str] = None
    items_synced: int = 0
    items_created: int = 0
    items_updated: int = 0


class SyncJobEnqueued(BaseModel):
    """Response when a sync job is enqueued."""

    job_id: UUID
    status: SyncJobStatus
    message: str
    accepted: bool = True  # Always true when 202
    deduplicated: bool = False  # True when returning existing queued/running job


# ============================================================================
# Sync Status Schema (canonical status endpoint payload)
# ============================================================================


class SyncStatus(BaseModel):
    """
    Rich sync status for a project.

    Distinguishes between:
    - Integration configured: credentials are set in backend settings
    - Project linked: project has URL/key/ID to connect to integration
    """

    project_id: UUID
    last_synced_at: Optional[datetime] = None

    # Integration configured (from backend settings/credentials)
    jira_integration_configured: bool
    precursive_integration_configured: bool

    # Project linked (project has URL/key/ID for the integration)
    jira_project_linked: bool
    precursive_project_linked: bool

    # Project-level info (for display)
    jira_project_key: Optional[str] = None
    jira_project_name: Optional[str] = None

    # Active jobs (queued or running)
    jira_active_job: Optional[SyncJobSummary] = None
    precursive_active_job: Optional[SyncJobSummary] = None

    # Last completed jobs (succeeded or failed)
    jira_last_job: Optional[SyncJobSummary] = None
    precursive_last_job: Optional[SyncJobSummary] = None

    # Legacy compat fields (deprecated, use *_integration_configured instead)
    @property
    def jira_configured(self) -> bool:
        return self.jira_integration_configured

    @property
    def precursive_configured(self) -> bool:
        return self.precursive_integration_configured
