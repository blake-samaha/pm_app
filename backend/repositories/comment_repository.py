"""Comment repository for shared comment queries with author info."""

from typing import Dict, List, Tuple
from uuid import UUID

from sqlalchemy import func
from sqlmodel import Session, select

from models import Comment, User


class CommentRepository:
    """Repository for Comment model with author-joined queries."""

    def __init__(self, session: Session):
        self.session = session

    def list_for_action(self, action_item_id: UUID) -> List[Tuple[Comment, User]]:
        """
        Get all comments for an action item with their authors.
        Returns (Comment, User) tuples ordered by created_at ascending.
        """
        statement = (
            select(Comment, User)
            .join(User, Comment.user_id == User.id)  # type: ignore[arg-type]
            .where(Comment.action_item_id == action_item_id)
            .order_by(Comment.created_at.asc())  # type: ignore[union-attr]
        )
        return list(self.session.exec(statement).all())

    def list_for_risk(self, risk_id: UUID) -> List[Tuple[Comment, User]]:
        """
        Get all comments for a risk with their authors.
        Returns (Comment, User) tuples ordered by created_at ascending.
        """
        statement = (
            select(Comment, User)
            .join(User, Comment.user_id == User.id)  # type: ignore[arg-type]
            .where(Comment.risk_id == risk_id)
            .order_by(Comment.created_at.asc())  # type: ignore[union-attr]
        )
        return list(self.session.exec(statement).all())

    def create(self, comment: Comment) -> Comment:
        """Create a new comment."""
        self.session.add(comment)
        self.session.commit()
        self.session.refresh(comment)
        return comment

    def count_for_actions(self, action_ids: List[UUID]) -> Dict[UUID, int]:
        """
        Get comment counts for multiple action items in a single query.
        Returns a dict mapping action_item_id -> count.
        """
        if not action_ids:
            return {}

        statement = (
            select(Comment.action_item_id, func.count(Comment.id))
            .where(Comment.action_item_id.in_(action_ids))  # type: ignore[union-attr]
            .group_by(Comment.action_item_id)
        )
        rows = self.session.exec(statement).all()
        return {action_id: count for action_id, count in rows}
