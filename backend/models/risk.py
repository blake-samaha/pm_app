"""Risk model."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlmodel import Field, Relationship, SQLModel

from models import RiskImpact, RiskProbability, RiskStatus

if TYPE_CHECKING:
    from models.comment import Comment
    from models.project import Project


class Risk(SQLModel, table=True):
    """Risk model for project risk tracking."""

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    project_id: uuid.UUID = Field(foreign_key="project.id", index=True)
    title: str = Field(default="")
    description: str
    category: Optional[str] = None
    impact_rationale: Optional[str] = None
    date_identified: Optional[datetime] = None
    probability: RiskProbability
    impact: RiskImpact
    status: RiskStatus = Field(default=RiskStatus.OPEN)
    mitigation_plan: Optional[str] = None

    # Source tracking: "manual" for user-created, "precursive" for synced from Salesforce
    source: Optional[str] = Field(default="manual")

    # Resolution tracking (set when status changes to CLOSED or MITIGATED)
    decision_record: Optional[str] = None
    resolved_at: Optional[datetime] = None
    resolved_by_id: Optional[uuid.UUID] = Field(default=None, foreign_key="user.id")

    # Reopening tracking (set when a resolved risk is reopened)
    reopen_reason: Optional[str] = None
    reopened_at: Optional[datetime] = None
    reopened_by_id: Optional[uuid.UUID] = Field(default=None, foreign_key="user.id")

    # Relationships
    project: "Project" = Relationship(back_populates="risks")
    # Note: resolved_by and reopened_by relationships removed due to SQLModel
    # limitations with multiple FKs to the same table. Use resolved_by_id and
    # reopened_by_id foreign keys directly instead.
    comments: List["Comment"] = Relationship(back_populates="risk")
