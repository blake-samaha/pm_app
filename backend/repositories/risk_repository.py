"""Risk repository."""

from typing import List
from uuid import UUID

from sqlmodel import Session, col, select

from models import Risk, RiskStatus
from repositories.base import BaseRepository


class RiskRepository(BaseRepository[Risk]):
    """Repository for Risk model with specialized queries."""

    def __init__(self, session: Session):
        super().__init__(Risk, session)

    def get_by_project(self, project_id: UUID) -> List[Risk]:
        """Get all risks for a project."""
        statement = select(Risk).where(Risk.project_id == project_id)
        return list(self.session.exec(statement).all())

    def get_open_risks(self, project_id: UUID) -> List[Risk]:
        """Get only open risks for a project."""
        statement = select(Risk).where(
            Risk.project_id == project_id, Risk.status == RiskStatus.OPEN
        )
        return list(self.session.exec(statement).all())

    def get_by_status(self, project_id: UUID, status: RiskStatus) -> List[Risk]:
        """Get risks filtered by status."""
        statement = select(Risk).where(
            Risk.project_id == project_id, Risk.status == status
        )
        return list(self.session.exec(statement).all())

    def get_resolved_risks(self, project_id: UUID) -> List[Risk]:
        """Get resolved (closed or mitigated) risks for a project."""
        statement = select(Risk).where(
            Risk.project_id == project_id,
            col(Risk.status).in_([RiskStatus.CLOSED, RiskStatus.MITIGATED]),
        )
        return list(self.session.exec(statement).all())
