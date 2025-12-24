"""Sync Job model for tracking background sync operations."""

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from sqlmodel import Field, SQLModel


class SyncJobType(str, Enum):
    """Type of sync operation."""

    JIRA = "jira"
    PRECURSIVE = "precursive"
    FULL = "full"


class SyncJobStatus(str, Enum):
    """Status of sync job execution."""

    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class SyncJob(SQLModel, table=True):
    """
    Tracks sync operations for durability and status reporting.

    Jobs are created when a sync is requested and updated as the sync progresses.
    This allows the API to return 202 immediately and clients to poll for status.
    """

    __tablename__ = "syncjob"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    project_id: uuid.UUID = Field(foreign_key="project.id", index=True)
    job_type: SyncJobType
    status: SyncJobStatus = Field(default=SyncJobStatus.QUEUED)

    # Timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    # Tracking
    requested_by_user_id: Optional[uuid.UUID] = Field(
        default=None, foreign_key="user.id"
    )

    # Results
    error: Optional[str] = None
    items_synced: int = 0
    items_created: int = 0
    items_updated: int = 0

    # For Jira incremental sync
    last_sync_cursor: Optional[str] = None  # e.g., last JQL updated date
