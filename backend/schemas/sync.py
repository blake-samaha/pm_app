"""Sync-related schemas."""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import uuid


class SyncResult(BaseModel):
    """Result of a sync operation."""
    project_id: uuid.UUID
    
    # Jira sync results
    jira_synced: bool
    jira_items_synced: int
    jira_items_created: int
    jira_items_updated: int
    
    # Precursive sync results
    precursive_synced: bool
    financials_updated: bool
    
    # Errors encountered during sync
    errors: list[str]
    
    # Timestamp
    synced_at: datetime


class SyncStatus(BaseModel):
    """Current sync status for a project."""
    project_id: uuid.UUID
    last_synced_at: Optional[datetime]
    
    # Integration configuration status
    jira_configured: bool
    precursive_configured: bool
    
    # Last sync results (if available)
    last_jira_items_count: Optional[int] = None
    last_precursive_sync_success: Optional[bool] = None


class JiraSyncResult(BaseModel):
    """Result of syncing Jira issues only."""
    project_id: uuid.UUID
    items_synced: int
    items_created: int
    items_updated: int
    errors: list[str]
    synced_at: datetime


class PrecursiveSyncResult(BaseModel):
    """Result of syncing Precursive data only."""
    project_id: uuid.UUID
    synced: bool
    financials_updated: bool
    project_name: Optional[str] = None
    client_name: Optional[str] = None
    errors: list[str]
    synced_at: datetime

