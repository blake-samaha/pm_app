"""Action service for business logic."""

from typing import List, Optional
from uuid import UUID

from sqlmodel import Session

from exceptions import AuthorizationError, ResourceNotFoundError
from models import ActionItem, User, UserRole
from repositories.action_repository import ActionRepository
from repositories.project_repository import ProjectRepository
from schemas import ActionItemCreate


class ActionService:
    """Service layer for action item business logic."""

    def __init__(self, session: Session):
        self.session = session
        self.repository = ActionRepository(session)
        self.project_repository = ProjectRepository(session)

    def _check_project_access(self, project_id: UUID, user: User) -> None:
        """Verify user has access to the project. Raises AuthorizationError if not."""
        if user.role == UserRole.COGNITER:
            return  # Cogniters have access to all projects

        if not self.project_repository.user_has_access(project_id, user.id):
            raise AuthorizationError("You don't have access to this project")

    def get_action_by_id(self, action_id: UUID) -> ActionItem:
        """Get an action item by ID."""
        action = self.repository.get_by_id(action_id)
        if not action:
            raise ResourceNotFoundError(f"Action item with ID {action_id} not found")
        return action

    def get_project_actions(self, project_id: UUID, user: User) -> List[ActionItem]:
        """Get all action items for a project."""
        # Verify project exists
        project = self.project_repository.get_by_id(project_id)
        if not project:
            raise ResourceNotFoundError(f"Project with ID {project_id} not found")

        # Verify access
        self._check_project_access(project_id, user)

        return self.repository.get_by_project(project_id)

    def create_action(self, data: ActionItemCreate, user: User) -> ActionItem:
        """Create a new action item."""
        # Verify project exists
        project = self.project_repository.get_by_id(data.project_id)
        if not project:
            raise ResourceNotFoundError(f"Project with ID {data.project_id} not found")

        # Verify access
        self._check_project_access(data.project_id, user)

        action = ActionItem.model_validate(data)
        return self.repository.create(action)

    def update_action(
        self,
        action_id: UUID,
        user: User,
        title: Optional[str] = None,
        status: Optional[str] = None,
        assignee: Optional[str] = None,
        priority: Optional[str] = None,
    ) -> ActionItem:
        """Update an action item."""
        action = self.get_action_by_id(action_id)

        # Verify access to project
        self._check_project_access(action.project_id, user)

        # Update fields if provided
        if title is not None:
            action.title = title
        if status is not None:
            action.status = status
        if assignee is not None:
            action.assignee = assignee
        if priority is not None:
            action.priority = priority

        return self.repository.update(action)

    def delete_action(self, action_id: UUID, user: User) -> bool:
        """Delete an action item."""
        _ = self.get_action_by_id(action_id)

        # Only Cogniters can delete actions
        if user.role != UserRole.COGNITER:
            raise AuthorizationError("Only Cogniters can delete action items")

        return self.repository.delete(action_id)

    def get_by_jira_key(self, jira_key: str) -> Optional[ActionItem]:
        """Get an action item by Jira key."""
        return self.repository.get_by_jira_key(jira_key)

    def get_by_jira_id(self, jira_id: str) -> Optional[ActionItem]:
        """Get an action item by Jira internal ID."""
        return self.repository.get_by_jira_id(jira_id)
