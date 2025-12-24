"""Sync Job service for managing sync job lifecycle."""

from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID

import structlog
from sqlmodel import Session

from models import SyncJob, SyncJobStatus, SyncJobType
from repositories.sync_job_repository import SyncJobRepository

logger = structlog.get_logger()


class SyncJobService:
    """Service for managing sync job persistence and lifecycle."""

    def __init__(self, session: Session):
        self.session = session
        self.repository = SyncJobRepository(session)

    def get_by_id(self, job_id: UUID) -> Optional[SyncJob]:
        """Get a sync job by ID."""
        return self.repository.get_by_id(job_id)

    def get_running_job(
        self, project_id: UUID, job_type: SyncJobType
    ) -> Optional[SyncJob]:
        """
        Get a running or queued job of the same type for this project.

        Used to dedupe sync requests - if a job is already running/queued,
        return it instead of creating a new one.
        """
        return self.repository.get_running_job(project_id, job_type)

    def get_active_job(
        self, project_id: UUID, job_type: SyncJobType
    ) -> Optional[SyncJob]:
        """Get an active job (queued or running) for this project and type."""
        return self.repository.get_active_job(project_id, job_type)

    def get_last_completed_job(
        self, project_id: UUID, job_type: SyncJobType
    ) -> Optional[SyncJob]:
        """Get the most recent completed job (succeeded or failed)."""
        return self.repository.get_last_completed_job(project_id, job_type)

    def get_last_successful_job(
        self, project_id: UUID, job_type: SyncJobType
    ) -> Optional[SyncJob]:
        """Get the most recent successful job for incremental sync."""
        return self.repository.get_last_successful_job(project_id, job_type)

    def get_jobs_for_project(self, project_id: UUID, limit: int = 10) -> List[SyncJob]:
        """Get recent sync jobs for a project."""
        return self.repository.get_jobs_for_project(project_id, limit)

    def create_job(
        self,
        project_id: UUID,
        job_type: SyncJobType,
        user_id: UUID,
    ) -> SyncJob:
        """
        Create a new sync job in queued state.

        Returns the created job with ID populated.
        """
        job = SyncJob(
            project_id=project_id,
            job_type=job_type,
            status=SyncJobStatus.QUEUED,
            requested_by_user_id=user_id,
        )
        self.session.add(job)
        self.session.commit()
        self.session.refresh(job)

        logger.info(
            "Sync job created",
            job_id=str(job.id),
            project_id=str(project_id),
            job_type=job_type,
        )

        return job

    def mark_running(self, job: SyncJob) -> None:
        """Mark a job as running with started_at timestamp."""
        job.status = SyncJobStatus.RUNNING
        job.started_at = datetime.now(timezone.utc)
        self.session.add(job)
        self.session.commit()

    def mark_succeeded(self, job: SyncJob, items_synced: int = 0) -> None:
        """Mark a job as succeeded with completion timestamp."""
        job.status = SyncJobStatus.SUCCEEDED
        job.items_synced = items_synced
        job.completed_at = datetime.now(timezone.utc)
        self.session.add(job)
        self.session.commit()

    def mark_failed(self, job: SyncJob, error: str, items_synced: int = 0) -> None:
        """Mark a job as failed with error message and completion timestamp."""
        job.status = SyncJobStatus.FAILED
        job.error = error
        job.items_synced = items_synced
        job.completed_at = datetime.now(timezone.utc)
        self.session.add(job)
        self.session.commit()

    def enqueue_or_get_existing(
        self,
        project_id: UUID,
        job_type: SyncJobType,
        user_id: UUID,
    ) -> tuple[SyncJob, bool]:
        """
        Create and enqueue a sync job, or return existing running job.

        Implements job deduplication - if a job of the same type is already
        running for this project, returns that job instead of creating a new one.

        Returns:
            Tuple of (job, deduplicated) where deduplicated is True if returning
            an existing queued/running job.
        """
        # Check for existing running job (deduplication)
        existing_job = self.get_running_job(project_id, job_type)
        if existing_job:
            logger.info(
                "Returning existing running job",
                job_id=str(existing_job.id),
                job_type=job_type,
            )
            return existing_job, True

        # Create new job
        job = self.create_job(project_id, job_type, user_id)
        return job, False
