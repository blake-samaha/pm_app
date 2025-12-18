"""Projects router."""

from typing import List
from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from dependencies import CogniterUser, CurrentUser, ProjectServiceDep, UserServiceDep
from exceptions import AuthorizationError, DuplicateResourceError, ResourceNotFoundError
from schemas import (
    InviteUserRequest,
    InviteUserResponse,
    ProjectCreate,
    ProjectRead,
    ProjectUpdate,
    UserRead,
)

router = APIRouter(
    prefix="/projects",
    tags=["projects"],
)


@router.get("/", response_model=List[ProjectRead])
async def list_projects(current_user: CurrentUser, project_service: ProjectServiceDep):
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
    project_service: ProjectServiceDep,
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
    project_id: UUID, current_user: CurrentUser, project_service: ProjectServiceDep
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
                detail="You don't have access to this project",
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
    project_service: ProjectServiceDep,
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
    project_service: ProjectServiceDep,
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
    project_id: UUID, current_user: CogniterUser, project_service: ProjectServiceDep
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
    project_id: UUID, current_user: CogniterUser, project_service: ProjectServiceDep
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


@router.get("/{project_id}/users", response_model=List[UserRead])
async def get_project_users(
    project_id: UUID,
    current_user: CogniterUser,  # Only Cogniters can view project users
    project_service: ProjectServiceDep,
):
    """
    Get all users assigned to a project.
    Only Cogniters can access this endpoint.
    """
    try:
        return project_service.get_project_users(project_id)
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/{project_id}/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def assign_user_to_project(
    project_id: UUID,
    user_id: UUID,
    current_user: CogniterUser,
    project_service: ProjectServiceDep,
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
    project_service: ProjectServiceDep,
):
    """
    Remove a user from a project.
    Only Cogniters can remove users.
    """
    try:
        project_service.remove_user_from_project(project_id, user_id, current_user)
    except AuthorizationError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.post("/{project_id}/invite", response_model=InviteUserResponse)
async def invite_user_to_project(
    project_id: UUID,
    invite_data: InviteUserRequest,
    current_user: CogniterUser,
    project_service: ProjectServiceDep,
    user_service: UserServiceDep,
):
    """
    Invite a user to a project by email.
    - If the email exists: assigns the user directly
    - If the email doesn't exist: creates a placeholder user and assigns them

    Only Cogniters can invite users.
    """
    # Verify project exists
    try:
        project_service.get_project_by_id(project_id)
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    email = invite_data.email.lower().strip()

    # Check if user exists
    existing_user = user_service.get_user_by_email(email)

    if existing_user:
        # User exists - just assign them
        try:
            project_service.assign_user_to_project(
                project_id, existing_user.id, current_user
            )
            return InviteUserResponse(
                user=UserRead.model_validate(existing_user),
                was_created=False,
                message=f"{existing_user.name} has been assigned to the project.",
            )
        except DuplicateResourceError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"{existing_user.name} is already assigned to this project.",
            )
    else:
        # Create placeholder user and assign
        try:
            new_user = user_service.create_pending_user(email)
            project_service.assign_user_to_project(
                project_id, new_user.id, current_user
            )
            return InviteUserResponse(
                user=UserRead.model_validate(new_user),
                was_created=True,
                message=f"Invitation created for {email}. They will have access once they register.",
            )
        except DuplicateResourceError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
