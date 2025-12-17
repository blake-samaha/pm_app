from datetime import datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel

class SyncResult(BaseModel):
    project_id: UUID
    jira_synced: bool
    jira_items_synced: int
    jira_items_created: int
    jira_items_updated: int
    precursive_synced: bool
    financials_updated: bool
    errors: List[str]
    synced_at: datetime

class JiraSyncResult(BaseModel):
    project_id: UUID
    items_synced: int
    items_created: int
    items_updated: int
    errors: List[str]
    synced_at: datetime

class PrecursiveSyncResult(BaseModel):
    project_id: UUID
    synced: bool
    financials_updated: bool
    project_name: Optional[str] = None
    client_name: Optional[str] = None
    errors: List[str]
    synced_at: datetime

class SyncStatus(BaseModel):
    project_id: UUID
    last_synced_at: Optional[datetime] = None
    jira_configured: bool
    precursive_configured: bool
    last_jira_items_count: Optional[int] = None
    last_precursive_sync_success: Optional[bool] = None
    jira_project_key: Optional[str] = None
    jira_project_name: Optional[str] = None
