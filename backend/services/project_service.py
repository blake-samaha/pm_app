"""Project service for business logic."""

from typing import List
from uuid import UUID

from sqlmodel import Session

from exceptions import AuthorizationError, DuplicateResourceError, ResourceNotFoundError
from models import Project, User
from permissions import (
    can_create_project,
    can_edit_project,
    can_manage_team,
    can_publish_project,
    is_internal_user,
)
from repositories.project_repository import ProjectRepository
from schemas.project import ProjectCreate, ProjectUpdate


class ProjectService:
    """Service layer for project-related business logic."""

    def __init__(self, session: Session):
        self.repository = ProjectRepository(session)
        self.session = session

    def get_project_by_id(self, project_id: UUID) -> Project:
        """Get project by ID."""
        project = self.repository.get_by_id(project_id)
        if not project:
            raise ResourceNotFoundError(f"Project with ID {project_id} not found")
        return project

    def get_all_projects(self) -> List[Project]:
        """Get all projects."""
        return self.repository.get_all()

    def get_published_projects(self) -> List[Project]:
        """Get all published projects."""
        return self.repository.get_published_projects()

    def get_user_projects(self, user: User) -> List[Project]:
        """Get projects accessible to a user."""
        if is_internal_user(user):
            # Cogniters see all projects
            return self.repository.get_all()
        else:
            # Clients only see assigned projects
            return self.repository.get_user_projects(user.id)

    def create_project(self, project_data: ProjectCreate, creator: User) -> Project:
        """Create a new project."""
        # Only Cogniters can create projects
        if not can_create_project(creator):
            raise AuthorizationError("Only Cogniters can create projects")

        # Check for duplicate Precursive URL
        if project_data.precursive_url and self.repository.precursive_url_exists(
            project_data.precursive_url
        ):
            raise DuplicateResourceError(
                f"Project with Precursive URL {project_data.precursive_url} already exists"
            )

        # Create project
        project = Project.model_validate(project_data)
        return self.repository.create(project)

    def update_project(
        self, project_id: UUID, project_data: ProjectUpdate, user: User
    ) -> Project:
        """Update an existing project."""
        # Only Cogniters can update projects
        if not can_edit_project(user):
            raise AuthorizationError("Only Cogniters can update projects")

        project = self.get_project_by_id(project_id)

        # Update fields
        update_dict = project_data.model_dump(exclude_unset=True)
        for key, value in update_dict.items():
            setattr(project, key, value)

        return self.repository.update(project)

    def delete_project(self, project_id: UUID, user: User) -> bool:
        """Delete a project."""
        # Only Cogniters can delete projects
        if not can_edit_project(user):
            raise AuthorizationError("Only Cogniters can delete projects")

        return self.repository.delete(project_id)

    def assign_user_to_project(
        self, project_id: UUID, user_id: UUID, assigner: User
    ) -> None:
        """Assign a user to a project."""
        # Only Cogniters can assign users
        if not can_manage_team(assigner):
            raise AuthorizationError("Only Cogniters can assign users to projects")

        # Verify project exists
        self.get_project_by_id(project_id)

        self.repository.add_user_to_project(project_id, user_id)

    def remove_user_from_project(
        self, project_id: UUID, user_id: UUID, remover: User
    ) -> None:
        """Remove a user from a project."""
        # Only Cogniters can remove users
        if not can_manage_team(remover):
            raise AuthorizationError("Only Cogniters can remove users from projects")

        self.repository.remove_user_from_project(project_id, user_id)

    def user_has_access_to_project(self, project_id: UUID, user: User) -> bool:
        """Check if a user has access to a project."""
        if is_internal_user(user):
            # Cogniters have access to all projects
            return True

        # Clients need to be assigned
        return self.repository.user_has_access(project_id, user.id)

    def get_project_users(self, project_id: UUID) -> List[User]:
        """Get all users assigned to a project."""
        # Verify project exists
        self.get_project_by_id(project_id)
        return self.repository.get_project_users(project_id)

    def publish_project(self, project_id: UUID, user: User) -> Project:
        """Publish a project."""
        if not can_publish_project(user):
            raise AuthorizationError("Only Cogniters can publish projects")

        project = self.get_project_by_id(project_id)
        project.is_published = True
        return self.repository.update(project)

    def unpublish_project(self, project_id: UUID, user: User) -> Project:
        """Unpublish a project."""
        if not can_publish_project(user):
            raise AuthorizationError("Only Cogniters can unpublish projects")

        project = self.get_project_by_id(project_id)
        project.is_published = False
        return self.repository.update(project)
