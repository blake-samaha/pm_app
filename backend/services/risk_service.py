"""Risk service for business logic."""

from datetime import datetime, timezone
from typing import List
from uuid import UUID

from sqlmodel import Session

from exceptions import AuthorizationError, ResourceNotFoundError, ValidationError
from models import Comment, Risk, RiskStatus, User, UserRole
from permissions import can_reopen_risk, can_resolve_risk
from repositories.project_repository import ProjectRepository
from repositories.risk_repository import RiskRepository
from schemas import RiskCreate, RiskUpdate


class RiskService:
    """Service layer for risk-related business logic."""

    def __init__(self, session: Session):
        self.session = session
        self.repository = RiskRepository(session)
        self.project_repository = ProjectRepository(session)

    def _check_project_access(self, project_id: UUID, user: User) -> None:
        """Verify user has access to the project. Raises AuthorizationError if not."""
        if user.role == UserRole.COGNITER:
            return  # Cogniters have access to all projects

        if not self.project_repository.user_has_access(project_id, user.id):
            raise AuthorizationError("You don't have access to this project")

    def get_risk_by_id(self, risk_id: UUID) -> Risk:
        """Get a risk by ID."""
        risk = self.repository.get_by_id(risk_id)
        if not risk:
            raise ResourceNotFoundError(f"Risk with ID {risk_id} not found")
        return risk

    def get_project_risks(self, project_id: UUID, user: User) -> List[Risk]:
        """Get all risks for a project."""
        # Verify project exists
        project = self.project_repository.get_by_id(project_id)
        if not project:
            raise ResourceNotFoundError(f"Project with ID {project_id} not found")

        # Verify access
        self._check_project_access(project_id, user)

        return self.repository.get_by_project(project_id)

    def create_risk(self, data: RiskCreate, user: User) -> Risk:
        """Create a new risk."""
        # Verify project exists
        project = self.project_repository.get_by_id(data.project_id)
        if not project:
            raise ResourceNotFoundError(f"Project with ID {data.project_id} not found")

        # Verify access
        self._check_project_access(data.project_id, user)

        risk = Risk.model_validate(data)
        return self.repository.create(risk)

    def update_risk(self, risk_id: UUID, data: RiskUpdate, user: User) -> Risk:
        """Update a risk's details (not status)."""
        risk = self.get_risk_by_id(risk_id)

        # Verify access
        self._check_project_access(risk.project_id, user)

        # Only Cogniters can update risks
        if user.role != UserRole.COGNITER:
            raise AuthorizationError("Only Cogniters can update risks")

        # Update fields
        update_dict = data.model_dump(exclude_unset=True)
        for key, value in update_dict.items():
            setattr(risk, key, value)

        return self.repository.update(risk)

    def resolve_risk(
        self, risk_id: UUID, status: RiskStatus, decision_record: str, user: User
    ) -> Risk:
        """
        Resolve a risk with a decision record.

        Business Rules:
        - Only Cogniters can resolve risks
        - Status must be CLOSED or MITIGATED
        - Decision record is required
        - Sets resolved_at and resolved_by automatically
        - Clears any previous reopen fields
        """
        risk = self.get_risk_by_id(risk_id)

        # Verify access to project
        self._check_project_access(risk.project_id, user)

        # Only Cogniters can resolve risks
        if not can_resolve_risk(user):
            raise AuthorizationError("Only Cogniters can resolve risks")

        # Validate status
        if status not in (RiskStatus.CLOSED, RiskStatus.MITIGATED):
            raise ValidationError("Status must be CLOSED or MITIGATED when resolving")

        # Validate decision record
        if not decision_record or not decision_record.strip():
            raise ValidationError("Decision record is required when resolving a risk")

        # Update the risk
        risk.status = status
        risk.decision_record = decision_record.strip()
        risk.resolved_at = datetime.now(timezone.utc)
        risk.resolved_by_id = user.id

        # Clear reopen fields (fresh resolution)
        risk.reopen_reason = None
        risk.reopened_at = None
        risk.reopened_by_id = None

        return self.repository.update(risk)

    def reopen_risk(self, risk_id: UUID, reason: str, user: User) -> Risk:
        """
        Reopen a previously resolved risk.

        Business Rules:
        - Only Cogniters can reopen risks
        - Reason is required
        - Sets reopened_at and reopened_by automatically
        - Changes status back to OPEN
        """
        risk = self.get_risk_by_id(risk_id)

        # Verify access to project
        self._check_project_access(risk.project_id, user)

        # Only Cogniters can reopen risks
        if not can_reopen_risk(user):
            raise AuthorizationError("Only Cogniters can reopen risks")

        # Validate the risk is currently resolved
        if risk.status == RiskStatus.OPEN:
            raise ValidationError("Risk is already open")

        # Validate reason
        if not reason or not reason.strip():
            raise ValidationError("Reason is required when reopening a risk")

        # Update the risk
        risk.status = RiskStatus.OPEN
        risk.reopen_reason = reason.strip()
        risk.reopened_at = datetime.now(timezone.utc)
        risk.reopened_by_id = user.id

        # Keep decision_record and resolved_* for history

        return self.repository.update(risk)

    def add_comment(self, risk_id: UUID, content: str, user: User) -> Comment:
        """
        Add a comment to a risk.

        Both Cogniters and assigned Clients can comment on risks.
        """
        risk = self.get_risk_by_id(risk_id)

        # Verify access to project
        self._check_project_access(risk.project_id, user)

        # Validate content
        if not content or not content.strip():
            raise ValidationError("Comment content is required")

        comment = Comment(risk_id=risk_id, user_id=user.id, content=content.strip())
        self.session.add(comment)
        self.session.commit()
        self.session.refresh(comment)
        return comment

    def get_comments(self, risk_id: UUID, user: User) -> List[Comment]:
        """Get all comments for a risk."""
        risk = self.get_risk_by_id(risk_id)

        # Verify access to project
        self._check_project_access(risk.project_id, user)

        return risk.comments

    def delete_risk(self, risk_id: UUID, user: User) -> bool:
        """Delete a risk."""
        _ = self.get_risk_by_id(risk_id)

        # Only Cogniters can delete risks
        if user.role != UserRole.COGNITER:
            raise AuthorizationError("Only Cogniters can delete risks")

        return self.repository.delete(risk_id)
