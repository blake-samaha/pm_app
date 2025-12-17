"""Risk model."""
from typing import Optional, TYPE_CHECKING
from sqlmodel import Field, SQLModel, Relationship
from datetime import datetime
import uuid

from models import RiskProbability, RiskImpact, RiskStatus

if TYPE_CHECKING:
    from models.project import Project


class Risk(SQLModel, table=True):
    """Risk model for project risk tracking."""
    
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    project_id: uuid.UUID = Field(foreign_key="project.id")
    title: str = Field(default="")
    description: str
    category: Optional[str] = None
    impact_rationale: Optional[str] = None
    date_identified: Optional[datetime] = None
    probability: RiskProbability
    impact: RiskImpact
    status: RiskStatus = Field(default=RiskStatus.OPEN)
    mitigation_plan: Optional[str] = None
    
    # Relationships
    project: "Project" = Relationship(back_populates="risks")
