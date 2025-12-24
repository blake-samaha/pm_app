"""Sync Job repository."""

from typing import List, Optional
from uuid import UUID

from sqlmodel import Session, select

from models import SyncJob, SyncJobStatus, SyncJobType
from repositories.base import BaseRepository


class SyncJobRepository(BaseRepository[SyncJob]):
    """Repository for SyncJob model with specialized queries."""

    def __init__(self, session: Session):
        super().__init__(SyncJob, session)

    def get_running_job(
        self, project_id: UUID, job_type: SyncJobType
    ) -> Optional[SyncJob]:
        """
        Get a running or queued job of the same type for this project.

        Used to dedupe sync requests - if a job is already running/queued,
        return it instead of creating a new one.
        """
        statement = select(SyncJob).where(
            SyncJob.project_id == project_id,
            SyncJob.job_type == job_type,
            SyncJob.status.in_([SyncJobStatus.QUEUED, SyncJobStatus.RUNNING]),  # type: ignore[union-attr]
        )
        return self.session.exec(statement).first()

    def get_last_successful_job(
        self, project_id: UUID, job_type: SyncJobType
    ) -> Optional[SyncJob]:
        """
        Get the most recent successful job for incremental sync.

        Returns the job with completed_at for calculating the sync window.
        """
        statement = (
            select(SyncJob)
            .where(
                SyncJob.project_id == project_id,
                SyncJob.job_type == job_type,
                SyncJob.status == SyncJobStatus.SUCCEEDED,
            )
            .order_by(SyncJob.completed_at.desc())  # type: ignore[union-attr]
            .limit(1)
        )
        return self.session.exec(statement).first()

    def get_jobs_for_project(self, project_id: UUID, limit: int = 10) -> List[SyncJob]:
        """Get recent sync jobs for a project."""
        statement = (
            select(SyncJob)
            .where(SyncJob.project_id == project_id)
            .order_by(SyncJob.created_at.desc())  # type: ignore[union-attr]
            .limit(limit)
        )
        return list(self.session.exec(statement).all())

    def get_pending_jobs(self) -> List[SyncJob]:
        """Get all queued jobs awaiting execution."""
        statement = (
            select(SyncJob)
            .where(SyncJob.status == SyncJobStatus.QUEUED)
            .order_by(SyncJob.created_at.asc())  # type: ignore[union-attr]
        )
        return list(self.session.exec(statement).all())

    def get_active_job(
        self, project_id: UUID, job_type: SyncJobType
    ) -> Optional[SyncJob]:
        """
        Get an active job (queued or running) for this project and type.

        Used for status card display.
        """
        return self.get_running_job(project_id, job_type)

    def get_last_completed_job(
        self, project_id: UUID, job_type: SyncJobType
    ) -> Optional[SyncJob]:
        """
        Get the most recent completed job (succeeded or failed) for this project and type.

        Used for status card display of last sync outcome.
        """
        statement = (
            select(SyncJob)
            .where(
                SyncJob.project_id == project_id,
                SyncJob.job_type == job_type,
                SyncJob.status.in_([SyncJobStatus.SUCCEEDED, SyncJobStatus.FAILED]),  # type: ignore[union-attr]
            )
            .order_by(SyncJob.completed_at.desc())  # type: ignore[union-attr]
            .limit(1)
        )
        return self.session.exec(statement).first()
