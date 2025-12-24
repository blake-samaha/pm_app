"""Action service for business logic."""

from typing import List, Optional, Tuple
from uuid import UUID

from sqlmodel import Session

from exceptions import AuthorizationError, ResourceNotFoundError, ValidationError
from models import ActionItem, Comment, Project, User
from permissions import can_delete_action, is_internal_user
from repositories.action_repository import ActionRepository
from repositories.comment_repository import CommentRepository
from repositories.project_repository import ProjectRepository
from schemas import ActionItemCreate


class ActionService:
    """Service layer for action item business logic."""

    def __init__(self, session: Session):
        self.session = session
        self.repository = ActionRepository(session)
        self.project_repository = ProjectRepository(session)
        self.comment_repository = CommentRepository(session)

    def _check_project_access(self, project: Project, user: User) -> None:
        """Verify user has access to the project. Raises AuthorizationError if not.

        Note: Project must be pre-fetched by caller to avoid duplicate queries.
        """
        if is_internal_user(user):
            return  # Cogniters have access to all projects

        if not project.is_published:
            raise AuthorizationError("This project is not published")

        # project.id is guaranteed to be set after fetching from DB
        assert project.id is not None
        if not self.project_repository.user_has_access(project.id, user.id):
            raise AuthorizationError("You don't have access to this project")

    def get_action_by_id(self, action_id: UUID) -> ActionItem:
        """Get an action item by ID (no access check)."""
        action = self.repository.get_by_id(action_id)
        if not action:
            raise ResourceNotFoundError(f"Action item with ID {action_id} not found")
        return action

    def get_action_for_user(self, action_id: UUID, user: User) -> ActionItem:
        """Get an action item by ID with access check.

        This is the public method routers should use when fetching a single action.
        It verifies the user has access to the action's project before returning.
        """
        action = self.get_action_by_id(action_id)

        # Fetch project for access check
        project = self.project_repository.get_by_id(action.project_id)
        if not project:
            raise ResourceNotFoundError(
                f"Project with ID {action.project_id} not found"
            )

        # Verify access to project
        self._check_project_access(project, user)

        return action

    def get_action_with_comment_count(
        self, action_id: UUID, user: User
    ) -> Tuple[ActionItem, int]:
        """Get an action item by ID with access check and comment count.

        Returns a tuple of (action, comment_count) for use in serialization.
        """
        action = self.get_action_for_user(action_id, user)
        counts = self.comment_repository.count_for_actions([action.id])
        return action, counts.get(action.id, 0)

    def get_project_actions(self, project_id: UUID, user: User) -> List[ActionItem]:
        """Get all action items for a project."""
        # Verify project exists
        project = self.project_repository.get_by_id(project_id)
        if not project:
            raise ResourceNotFoundError(f"Project with ID {project_id} not found")

        # Verify access (pass already-fetched project)
        self._check_project_access(project, user)

        return self.repository.get_by_project(project_id)

    def get_project_actions_with_comment_counts(
        self, project_id: UUID, user: User
    ) -> List[Tuple[ActionItem, int]]:
        """Get all action items for a project with their comment counts."""
        actions = self.get_project_actions(project_id, user)
        if not actions:
            return []

        action_ids = [a.id for a in actions]
        counts = self.comment_repository.count_for_actions(action_ids)
        return [(action, counts.get(action.id, 0)) for action in actions]

    def get_project_actions_paginated(
        self,
        project_id: UUID,
        user: User,
        limit: int = 25,
        offset: int = 0,
        search: Optional[str] = None,
        statuses: Optional[List[str]] = None,
    ) -> Tuple[List[Tuple[ActionItem, int]], int]:
        """
        Get paginated action items for a project with their comment counts.

        Args:
            project_id: The project UUID
            user: The requesting user
            limit: Maximum number of results (default 25)
            offset: Number of results to skip (default 0)
            search: Optional search term for title or jira_id
            statuses: Optional list of status strings to filter by

        Returns:
            Tuple of (list of (action, comment_count) tuples, total count)
        """
        from models import ActionStatus

        # Verify project exists and user has access
        project = self.project_repository.get_by_id(project_id)
        if not project:
            raise ResourceNotFoundError(f"Project with ID {project_id} not found")
        self._check_project_access(project, user)

        # Convert status strings to enum values
        status_enums = None
        if statuses:
            try:
                status_enums = [ActionStatus(s) for s in statuses]
            except ValueError:
                pass  # Invalid status values are ignored

        # Get paginated actions
        actions, total = self.repository.page_by_project(
            project_id=project_id,
            limit=limit,
            offset=offset,
            search=search,
            statuses=status_enums,
        )

        if not actions:
            return [], total

        # Get comment counts only for this page
        action_ids = [a.id for a in actions]
        counts = self.comment_repository.count_for_actions(action_ids)
        items_with_counts = [(action, counts.get(action.id, 0)) for action in actions]

        return items_with_counts, total

    def create_action(self, data: ActionItemCreate, user: User) -> ActionItem:
        """Create a new action item."""
        # Verify project exists
        project = self.project_repository.get_by_id(data.project_id)
        if not project:
            raise ResourceNotFoundError(f"Project with ID {data.project_id} not found")

        # Verify access (pass already-fetched project)
        self._check_project_access(project, user)

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

        # Fetch project for access check
        project = self.project_repository.get_by_id(action.project_id)
        if not project:
            raise ResourceNotFoundError(
                f"Project with ID {action.project_id} not found"
            )

        # Verify access to project
        self._check_project_access(project, user)

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
        if not can_delete_action(user):
            raise AuthorizationError("Only Cogniters can delete action items")

        return self.repository.delete(action_id)

    def get_by_jira_key(self, jira_key: str) -> Optional[ActionItem]:
        """Get an action item by Jira key."""
        return self.repository.get_by_jira_key(jira_key)

    def get_by_jira_id(self, jira_id: str) -> Optional[ActionItem]:
        """Get an action item by Jira internal ID."""
        return self.repository.get_by_jira_id(jira_id)

    # =========================================================================
    # Comment Methods
    # =========================================================================

    def get_comments(self, action_id: UUID, user: User) -> List[Tuple[Comment, User]]:
        """
        Get all comments for an action item.

        Both Cogniters and assigned Clients can view comments.
        """
        action = self.get_action_by_id(action_id)

        # Fetch project for access check
        project = self.project_repository.get_by_id(action.project_id)
        if not project:
            raise ResourceNotFoundError(
                f"Project with ID {action.project_id} not found"
            )

        # Verify access to project
        self._check_project_access(project, user)

        # Get comments with authors
        return self.comment_repository.list_for_action(action_id)

    def add_comment(
        self, action_id: UUID, content: str, user: User
    ) -> Tuple[Comment, User]:
        """
        Add a comment to an action item.

        Both Cogniters and assigned Clients can comment on actions.
        """
        action = self.get_action_by_id(action_id)

        # Fetch project for access check
        project = self.project_repository.get_by_id(action.project_id)
        if not project:
            raise ResourceNotFoundError(
                f"Project with ID {action.project_id} not found"
            )

        # Verify access to project
        self._check_project_access(project, user)

        # Validate content
        if not content or not content.strip():
            raise ValidationError("Comment content is required")

        # Create and persist the comment
        comment = Comment(
            action_item_id=action_id,
            user_id=user.id,
            content=content.strip(),
        )
        comment = self.comment_repository.create(comment)

        return comment, user
