"""Sync router for triggering data synchronization."""

import uuid

import structlog
from fastapi import APIRouter, BackgroundTasks, HTTPException, status

from config import get_settings
from database import get_session_context
from dependencies import (
    CogniterUser,
    CurrentUser,
    ProjectServiceDep,
    SessionDep,
    SettingsDep,
    SyncJobServiceDep,
)
from exceptions import IntegrationError, ResourceNotFoundError
from models import Project, SyncJob, SyncJobType
from permissions import is_internal_user
from schemas.sync import (
    SyncJobEnqueued,
    SyncJobRead,
    SyncResult,
    SyncStatus,
)
from services.sync_job_service import SyncJobService
from services.sync_service import SyncService

logger = structlog.get_logger()

router = APIRouter(
    prefix="/sync",
    tags=["sync"],
)


# ============================================================================
# Background Job Execution
# ============================================================================


async def run_sync_job(job_id: uuid.UUID, job_type: SyncJobType):
    """
    Execute a sync job in the background with a fresh database session.

    This function creates its own database session to avoid holding onto
    the request-scoped session which may be closed.
    """
    settings = get_settings()

    # Use context manager for session to ensure proper cleanup
    with get_session_context() as session:
        sync_job_service = SyncJobService(session)
        job = sync_job_service.get_by_id(job_id)

        if not job:
            logger.error("Sync job not found", job_id=str(job_id))
            return

        # Mark job as running
        sync_job_service.mark_running(job)

        items_synced = 0
        error_message = None

        try:
            # Get the project
            project = session.get(Project, job.project_id)
            if not project:
                raise ResourceNotFoundError(f"Project {job.project_id} not found")

            # Create sync service with fresh session
            sync_service = SyncService(session, settings)

            try:
                if job_type == SyncJobType.JIRA:
                    result = await sync_service.sync_jira_data(project)
                    items_synced = result.actions_count
                    if result.error:
                        error_message = result.error

                elif job_type == SyncJobType.PRECURSIVE:
                    result = await sync_service.sync_precursive_data(project)
                    items_synced = result.risks_count
                    if result.error:
                        error_message = result.error

                elif job_type == SyncJobType.FULL:
                    result = await sync_service.sync_project(job.project_id)
                    items_synced = (
                        result.jira.actions_count + result.precursive.risks_count
                    )
                    if result.jira.error or result.precursive.error:
                        errors = []
                        if result.jira.error:
                            errors.append(f"Jira: {result.jira.error}")
                        if result.precursive.error:
                            errors.append(f"Precursive: {result.precursive.error}")
                        error_message = "; ".join(errors)
            finally:
                await sync_service.close()

        except Exception as e:
            logger.error(
                "Sync job failed", job_id=str(job_id), error=str(e), exc_info=True
            )
            error_message = str(e)

        # Mark job as complete
        if error_message:
            sync_job_service.mark_failed(job, error_message, items_synced)
        else:
            sync_job_service.mark_succeeded(job, items_synced)

        logger.info(
            "Sync job completed",
            job_id=str(job_id),
            status=job.status,
            items_synced=job.items_synced,
        )


def enqueue_sync_job(
    sync_job_service: SyncJobService,
    project_id: uuid.UUID,
    job_type: SyncJobType,
    user_id: uuid.UUID,
    background_tasks: BackgroundTasks,
) -> tuple[SyncJob, bool]:
    """
    Create and enqueue a sync job, or return existing running job.

    Implements job deduplication - if a job of the same type is already
    running for this project, returns that job instead of creating a new one.

    Returns:
        Tuple of (job, deduplicated) where deduplicated is True if returning
        an existing queued/running job.
    """
    job, deduplicated = sync_job_service.enqueue_or_get_existing(
        project_id, job_type, user_id
    )

    if not deduplicated:
        # Schedule background execution for new jobs
        background_tasks.add_task(run_sync_job, job.id, job_type)

        logger.info(
            "Sync job enqueued",
            job_id=str(job.id),
            project_id=str(project_id),
            job_type=job_type,
        )

    return job, deduplicated


# ============================================================================
# Job Status Endpoint
# ============================================================================


@router.get("/jobs/{job_id}", response_model=SyncJobRead)
async def get_job_status(
    job_id: uuid.UUID,
    session: SessionDep,
    current_user: CurrentUser,
    project_service: ProjectServiceDep,
    sync_job_service: SyncJobServiceDep,
):
    """
    Get the status of a sync job.

    Poll this endpoint to check if a sync job has completed.
    User must have access to the project the job belongs to.
    """
    job = sync_job_service.get_by_id(job_id)

    if not job:
        raise HTTPException(status_code=404, detail="Sync job not found")

    # Enforce project access control
    project = session.get(Project, job.project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Check access: Cogniters see all, Clients need assignment + published
    if not is_internal_user(current_user):
        if not project.is_published:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This project is not published",
            )
        if not project_service.user_has_access_to_project(job.project_id, current_user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to this project",
            )

    return job


@router.post("/{project_id}", response_model=SyncResult)
async def trigger_sync(
    project_id: uuid.UUID,
    session: SessionDep,
    settings: SettingsDep,
    current_user: CogniterUser,  # Only Cogniters can trigger syncs
):
    """
    Trigger a full sync for a project (Jira + Precursive).
    Only Cogniters can trigger syncs.

    This endpoint will:
    1. Fetch issues from Jira and create/update ActionItems
    2. Fetch project data and financials from Precursive
    3. Update the project's last_synced_at timestamp

    Returns a SyncResult with details of what was synced.
    """
    logger.info("Sync requested", project_id=str(project_id), user=current_user.email)

    # Verify project exists
    project = session.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Run sync
    sync_service = SyncService(session, settings)
    try:
        result = await sync_service.sync_project(project_id)
        return result
    except IntegrationError as e:
        logger.error("Sync failed", project_id=str(project_id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e)
        )
    finally:
        await sync_service.close()


@router.post(
    "/{project_id}/jira",
    response_model=SyncJobEnqueued,
    status_code=status.HTTP_202_ACCEPTED,
)
async def sync_jira_only(
    project_id: uuid.UUID,
    session: SessionDep,
    settings: SettingsDep,
    background_tasks: BackgroundTasks,
    current_user: CogniterUser,  # Only Cogniters can trigger syncs
    sync_job_service: SyncJobServiceDep,
):
    """
    Trigger a Jira sync for a project.

    Returns 202 Accepted with a job ID. Poll GET /sync/jobs/{job_id} for status.
    If a sync is already running for this project, returns the existing job.
    """
    logger.info(
        "Jira sync requested", project_id=str(project_id), user=current_user.email
    )

    # Verify project exists
    project = session.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    sync_service = SyncService(session, settings)

    if not sync_service.jira.is_configured:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Jira integration is not configured. Set JIRA_BASE_URL, JIRA_EMAIL, and JIRA_API_TOKEN.",
        )

    # Enqueue the job
    job, deduplicated = enqueue_sync_job(
        sync_job_service=sync_job_service,
        project_id=project_id,
        job_type=SyncJobType.JIRA,
        user_id=current_user.id,
        background_tasks=background_tasks,
    )

    return SyncJobEnqueued(
        job_id=job.id,
        status=job.status,
        message="Jira sync already running"
        if deduplicated
        else "Jira sync job enqueued",
        accepted=True,
        deduplicated=deduplicated,
    )


@router.post(
    "/{project_id}/precursive",
    response_model=SyncJobEnqueued,
    status_code=status.HTTP_202_ACCEPTED,
)
async def sync_precursive_only(
    project_id: uuid.UUID,
    session: SessionDep,
    settings: SettingsDep,
    background_tasks: BackgroundTasks,
    current_user: CogniterUser,  # Only Cogniters can trigger syncs
    sync_job_service: SyncJobServiceDep,
):
    """
    Trigger a Precursive sync for a project.

    Returns 202 Accepted with a job ID. Poll GET /sync/jobs/{job_id} for status.
    If a sync is already running for this project, returns the existing job.
    """
    logger.info(
        "Precursive sync requested", project_id=str(project_id), user=current_user.email
    )

    # Verify project exists
    project = session.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    sync_service = SyncService(session, settings)

    if not sync_service.precursive.is_configured:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Precursive integration is not configured. Set PRECURSIVE_INSTANCE_URL and credentials.",
        )

    # Enqueue the job
    job, deduplicated = enqueue_sync_job(
        sync_job_service=sync_job_service,
        project_id=project_id,
        job_type=SyncJobType.PRECURSIVE,
        user_id=current_user.id,
        background_tasks=background_tasks,
    )

    return SyncJobEnqueued(
        job_id=job.id,
        status=job.status,
        message="Precursive sync already running"
        if deduplicated
        else "Precursive sync job enqueued",
        accepted=True,
        deduplicated=deduplicated,
    )


@router.get("/{project_id}/status", response_model=SyncStatus)
async def get_sync_status(
    project_id: uuid.UUID,
    session: SessionDep,
    settings: SettingsDep,
    current_user: CurrentUser,
    project_service: ProjectServiceDep,
):
    """
    Get the current sync status for a project.

    Returns information about:
    - When the project was last synced
    - Whether Jira and Precursive integrations are configured
    - Active and last completed jobs for each integration
    - Summary of last sync results

    User must have access to the project (Cogniters: all, Clients: assigned + published).
    """
    # Verify project exists
    project = session.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Enforce project access control
    if not is_internal_user(current_user):
        if not project.is_published:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This project is not published",
            )
        if not project_service.user_has_access_to_project(project_id, current_user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to this project",
            )

    # SyncService is needed for get_sync_status (uses jira/precursive is_configured)
    # Note: The API clients are only instantiated but not used for network calls here
    sync_service = SyncService(session, settings)

    try:
        sync_status = sync_service.get_sync_status(project_id)
        return sync_status
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
