from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


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


class SyncStatus(BaseModel):
    project_id: UUID
    last_synced_at: Optional[datetime] = None
    jira_configured: bool
    precursive_configured: bool
    jira_project_key: Optional[str] = None
    jira_project_name: Optional[str] = None
