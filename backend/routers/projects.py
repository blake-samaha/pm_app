"""Projects router."""

from typing import List
from uuid import UUID

from fastapi import APIRouter, status

from dependencies import CogniterUser, CurrentUser, ProjectServiceDep, UserServiceDep
from exceptions import AuthorizationError
from permissions import can_view_financials, is_internal_user
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


def _to_project_read(project, user) -> ProjectRead:
    """
    Serialize a project for the requesting user, enforcing field-level permissions.

    Frontend UI gating is not a security boundary; enforce financial visibility here.
    """
    model = ProjectRead.model_validate(project)
    if not can_view_financials(user):
        model.total_budget = None
        model.spent_budget = None
        model.remaining_budget = None
    return model


@router.get("/", response_model=List[ProjectRead])
async def list_projects(current_user: CurrentUser, project_service: ProjectServiceDep):
    """
    List all projects accessible to the current user.
    - Cogniters: see all projects
    - Clients: see only assigned projects
    """
    projects = project_service.get_user_projects(current_user)
    return [_to_project_read(p, current_user) for p in projects]


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
    # DuplicateResourceError -> 409, AuthorizationError -> 403 via global handlers
    project = project_service.create_project(project_data, current_user)
    return project


@router.get("/{project_id}", response_model=ProjectRead)
async def get_project(
    project_id: UUID, current_user: CurrentUser, project_service: ProjectServiceDep
):
    """
    Get a specific project by ID.
    User must have access to the project.
    """
    # ResourceNotFoundError -> 404 via global handler
    project = project_service.get_project_by_id(project_id)

    # Access rules:
    # - Cogniters: all projects
    # - Clients: must be assigned AND project must be published
    if not is_internal_user(current_user):
        if not project.is_published:
            raise AuthorizationError("This project is not published")
        if not project_service.user_has_access_to_project(project_id, current_user):
            raise AuthorizationError("You don't have access to this project")

    return _to_project_read(project, current_user)


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
    # ResourceNotFoundError -> 404, AuthorizationError -> 403 via global handlers
    project = project_service.update_project(project_id, project_data, current_user)
    return project


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
    # ResourceNotFoundError -> 404, AuthorizationError -> 403 via global handlers
    project_service.delete_project(project_id, current_user)


@router.post("/{project_id}/publish", response_model=ProjectRead)
async def publish_project(
    project_id: UUID, current_user: CogniterUser, project_service: ProjectServiceDep
):
    """
    Publish a project (make it visible to assigned clients).
    Only Cogniters can publish projects.
    """
    # ResourceNotFoundError -> 404, AuthorizationError -> 403 via global handlers
    project = project_service.publish_project(project_id, current_user)
    return project


@router.post("/{project_id}/unpublish", response_model=ProjectRead)
async def unpublish_project(
    project_id: UUID, current_user: CogniterUser, project_service: ProjectServiceDep
):
    """
    Unpublish a project (hide from clients).
    Only Cogniters can unpublish projects.
    """
    # ResourceNotFoundError -> 404, AuthorizationError -> 403 via global handlers
    project = project_service.unpublish_project(project_id, current_user)
    return project


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
    # ResourceNotFoundError -> 404 via global handler
    return project_service.get_project_users(project_id)


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
    # ResourceNotFoundError -> 404, AuthorizationError -> 403 via global handlers
    project_service.assign_user_to_project(project_id, user_id, current_user)


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
    # AuthorizationError -> 403 via global handler
    project_service.remove_user_from_project(project_id, user_id, current_user)


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
    # Verify project exists (ResourceNotFoundError -> 404 via global handler)
    project_service.get_project_by_id(project_id)

    email = invite_data.email.lower().strip()

    # Check if user exists
    existing_user = user_service.get_user_by_email(email)

    if existing_user:
        # User exists - just assign them
        # DuplicateResourceError -> 409 via global handler (user already assigned)
        project_service.assign_user_to_project(
            project_id, existing_user.id, current_user
        )
        return InviteUserResponse(
            user=UserRead.model_validate(existing_user),
            was_created=False,
            message=f"{existing_user.name} has been assigned to the project.",
        )
    else:
        # Create placeholder user and assign
        # DuplicateResourceError -> 409 via global handler
        new_user = user_service.create_pending_user(email)
        project_service.assign_user_to_project(project_id, new_user.id, current_user)
        return InviteUserResponse(
            user=UserRead.model_validate(new_user),
            was_created=True,
            message=f"Invitation created for {email}. They will have access once they register.",
        )
