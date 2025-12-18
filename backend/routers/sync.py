"""Sync router for triggering data synchronization."""

import uuid

import structlog
from fastapi import APIRouter, HTTPException, status

from dependencies import CurrentUser, SessionDep, SettingsDep
from exceptions import IntegrationError, ResourceNotFoundError
from models import Project, UserRole
from schemas.sync import JiraSyncResult, PrecursiveSyncResult, SyncResult, SyncStatus
from services.sync_service import SyncService

logger = structlog.get_logger()

router = APIRouter(
    prefix="/sync",
    tags=["sync"],
)


@router.post("/{project_id}", response_model=SyncResult)
async def trigger_sync(
    project_id: uuid.UUID,
    session: SessionDep,
    settings: SettingsDep,
    current_user: CurrentUser,
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

    # Only Cogniters can trigger sync
    if current_user.role == UserRole.CLIENT:
        raise HTTPException(status_code=403, detail="Clients cannot trigger sync")

    # Run sync
    sync_service = SyncService(session, settings)
    try:
        result = await sync_service.sync_project(project_id)
        return result
    except IntegrationError as e:
        logger.error("Sync failed", project_id=str(project_id), error=str(e))
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))


@router.post("/{project_id}/jira", response_model=JiraSyncResult)
async def sync_jira_only(
    project_id: uuid.UUID,
    session: SessionDep,
    settings: SettingsDep,
    current_user: CurrentUser,
):
    """
    Sync only Jira issues for a project.

    Fetches issues from Jira and creates/updates ActionItems.
    Does not sync Precursive data.
    """
    logger.info(
        "Jira sync requested", project_id=str(project_id), user=current_user.email
    )

    # Verify project exists
    project = session.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Only Cogniters can trigger sync
    if current_user.role == UserRole.CLIENT:
        raise HTTPException(status_code=403, detail="Clients cannot trigger sync")

    sync_service = SyncService(session, settings)

    if not sync_service.jira.is_configured:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Jira integration is not configured. Set JIRA_BASE_URL, JIRA_EMAIL, and JIRA_API_TOKEN.",
        )

    try:
        result = await sync_service.sync_jira_data(project)
        await sync_service.close()
        return result
    except IntegrationError as e:
        await sync_service.close()
        logger.error("Jira sync failed", project_id=str(project_id), error=str(e))
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))


@router.post("/{project_id}/precursive", response_model=PrecursiveSyncResult)
async def sync_precursive_only(
    project_id: uuid.UUID,
    session: SessionDep,
    settings: SettingsDep,
    current_user: CurrentUser,
):
    """
    Sync only Precursive data for a project.

    Fetches project details and financials from Precursive/Salesforce.
    Does not sync Jira issues.
    """
    logger.info(
        "Precursive sync requested", project_id=str(project_id), user=current_user.email
    )

    # Verify project exists
    project = session.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Only Cogniters can trigger sync
    if current_user.role == UserRole.CLIENT:
        raise HTTPException(status_code=403, detail="Clients cannot trigger sync")

    sync_service = SyncService(session, settings)

    if not sync_service.precursive.is_configured:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Precursive integration is not configured. Set PRECURSIVE_INSTANCE_URL and credentials.",
        )

    try:
        result = await sync_service.sync_precursive_data(project)
        await sync_service.close()
        return result
    except IntegrationError as e:
        await sync_service.close()
        logger.error("Precursive sync failed", project_id=str(project_id), error=str(e))
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))


@router.get("/{project_id}/status", response_model=SyncStatus)
async def get_sync_status(
    project_id: uuid.UUID,
    session: SessionDep,
    settings: SettingsDep,
    current_user: CurrentUser,
):
    """
    Get the current sync status for a project.

    Returns information about:
    - When the project was last synced
    - Whether Jira and Precursive integrations are configured
    - Summary of last sync results
    """
    # Verify project exists
    project = session.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    sync_service = SyncService(session, settings)

    try:
        status = sync_service.get_sync_status(project_id)
        return status
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
