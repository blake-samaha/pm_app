"""Action repository."""

from typing import List, Optional
from uuid import UUID

from sqlmodel import Session, select

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
