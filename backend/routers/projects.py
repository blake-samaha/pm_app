"""Projects router."""
from fastapi import APIRouter, HTTPException, status
from typing import List
from uuid import UUID

from schemas import ProjectCreate, ProjectRead, ProjectUpdate
from dependencies import (
    CurrentUser,
    CogniterUser,
    ProjectServiceDep
)
from exceptions import (
    ResourceNotFoundError,
    DuplicateResourceError,
    AuthorizationError
)

router = APIRouter(
    prefix="/projects",
    tags=["projects"],
)


@router.get("/", response_model=List[ProjectRead])
async def list_projects(
    current_user: CurrentUser,
    project_service: ProjectServiceDep
):
    """
    List all projects accessible to the current user.
    - Cogniters: see all projects
    - Clients: see only assigned projects
    """
    projects = project_service.get_user_projects(current_user)
    return projects


@router.post("/", response_model=ProjectRead, status_code=status.HTTP_201_CREATED)
async def create_project(
    project_data: ProjectCreate,
    current_user: CogniterUser,  # Only Cogniters can create
    project_service: ProjectServiceDep
):
    """
    Create a new project.
    Only Cogniters can create projects.
    """
    try:
        project = project_service.create_project(project_data, current_user)
        return project
    except DuplicateResourceError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except AuthorizationError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.get("/{project_id}", response_model=ProjectRead)
async def get_project(
    project_id: UUID,
    current_user: CurrentUser,
    project_service: ProjectServiceDep
):
    """
    Get a specific project by ID.
    User must have access to the project.
    """
    try:
        # Check access
        if not project_service.user_has_access_to_project(project_id, current_user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to this project"
            )
        
        project = project_service.get_project_by_id(project_id)
        return project
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.patch("/{project_id}", response_model=ProjectRead)
async def update_project(
    project_id: UUID,
    project_data: ProjectUpdate,
    current_user: CogniterUser,  # Only Cogniters can update
    project_service: ProjectServiceDep
):
    """
    Update a project.
    Only Cogniters can update projects.
    """
    try:
        project = project_service.update_project(project_id, project_data, current_user)
        return project
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except AuthorizationError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: UUID,
    current_user: CogniterUser,  # Only Cogniters can delete
    project_service: ProjectServiceDep
):
    """
    Delete a project.
    Only Cogniters can delete projects.
    """
    try:
        project_service.delete_project(project_id, current_user)
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except AuthorizationError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.post("/{project_id}/publish", response_model=ProjectRead)
async def publish_project(
    project_id: UUID,
    current_user: CogniterUser,
    project_service: ProjectServiceDep
):
    """
    Publish a project (make it visible to assigned clients).
    Only Cogniters can publish projects.
    """
    try:
        project = project_service.publish_project(project_id, current_user)
        return project
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except AuthorizationError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.post("/{project_id}/unpublish", response_model=ProjectRead)
async def unpublish_project(
    project_id: UUID,
    current_user: CogniterUser,
    project_service: ProjectServiceDep
):
    """
    Unpublish a project (hide from clients).
    Only Cogniters can unpublish projects.
    """
    try:
        project = project_service.unpublish_project(project_id, current_user)
        return project
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except AuthorizationError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.post("/{project_id}/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def assign_user_to_project(
    project_id: UUID,
    user_id: UUID,
    current_user: CogniterUser,
    project_service: ProjectServiceDep
):
    """
    Assign a user to a project.
    Only Cogniters can assign users.
    """
    try:
        project_service.assign_user_to_project(project_id, user_id, current_user)
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except AuthorizationError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.delete("/{project_id}/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_user_from_project(
    project_id: UUID,
    user_id: UUID,
    current_user: CogniterUser,
    project_service: ProjectServiceDep
):
    """
    Remove a user from a project.
    Only Cogniters can remove users.
    """
    try:
        project_service.remove_user_from_project(project_id, user_id, current_user)
    except AuthorizationError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
