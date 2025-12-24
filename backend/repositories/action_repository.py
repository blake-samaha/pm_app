"""Action repository."""

from typing import List, Optional, Tuple
from uuid import UUID

from sqlmodel import Session, col, func, select

from models import ActionItem, ActionStatus
from repositories.base import BaseRepository


class ActionRepository(BaseRepository[ActionItem]):
    """Repository for ActionItem model with specialized queries."""

    def __init__(self, session: Session):
        super().__init__(ActionItem, session)

    def get_by_project(self, project_id: UUID) -> List[ActionItem]:
        """Get all action items for a project."""
        statement = select(ActionItem).where(ActionItem.project_id == project_id)
        return list(self.session.exec(statement).all())

    def page_by_project(
        self,
        project_id: UUID,
        limit: int = 25,
        offset: int = 0,
        search: Optional[str] = None,
        statuses: Optional[List[ActionStatus]] = None,
    ) -> Tuple[List[ActionItem], int]:
        """
        Get paginated action items for a project with optional filtering.

        Args:
            project_id: The project UUID
            limit: Maximum number of results (default 25)
            offset: Number of results to skip (default 0)
            search: Optional search term for title or jira_id
            statuses: Optional list of statuses to filter by

        Returns:
            Tuple of (list of actions, total count matching filters)
        """
        # Build base query
        base_query = select(ActionItem).where(ActionItem.project_id == project_id)

        # Apply search filter
        if search:
            search_pattern = f"%{search}%"
            base_query = base_query.where(
                col(ActionItem.title).ilike(search_pattern)
                | col(ActionItem.jira_id).ilike(search_pattern)
            )

        # Apply status filter
        if statuses:
            base_query = base_query.where(col(ActionItem.status).in_(statuses))

        # Get total count (before pagination)
        count_query = select(func.count()).select_from(base_query.subquery())
        total = self.session.exec(count_query).one()

        # Apply pagination and ordering (order by id since ActionItem has no created_at)
        paginated_query = (
            base_query.order_by(ActionItem.id.desc())  # type: ignore[union-attr]
            .offset(offset)
            .limit(limit)
        )

        items = list(self.session.exec(paginated_query).all())
        return items, total

    def get_by_jira_key(self, jira_key: str) -> Optional[ActionItem]:
        """Get action item by Jira key."""
        statement = select(ActionItem).where(ActionItem.jira_key == jira_key)
        return self.session.exec(statement).first()

    def get_by_status(self, project_id: UUID, status: ActionStatus) -> List[ActionItem]:
        """Get action items filtered by status."""
        statement = select(ActionItem).where(
            ActionItem.project_id == project_id, ActionItem.status == status
        )
        return list(self.session.exec(statement).all())

    def get_by_assignee(self, project_id: UUID, assignee: str) -> List[ActionItem]:
        """Get action items assigned to a specific person."""
        statement = select(ActionItem).where(
            ActionItem.project_id == project_id, ActionItem.assignee == assignee
        )
        return list(self.session.exec(statement).all())

    def get_by_jira_id(self, jira_id: str) -> Optional[ActionItem]:
        """Get action item by Jira internal ID."""
        statement = select(ActionItem).where(ActionItem.jira_id == jira_id)
        return self.session.exec(statement).first()
