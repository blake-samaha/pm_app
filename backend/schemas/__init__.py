"""Schemas package - exports all Pydantic schemas."""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import uuid

from models import ActionStatus, Priority, RiskProbability, RiskImpact, RiskStatus

from schemas.auth import GoogleLoginRequest, Token
from schemas.user import UserRead, UserCreate
from schemas.project import ProjectBase, ProjectCreate, ProjectRead, ProjectUpdate
from schemas.sync import SyncResult, SyncStatus, JiraSyncResult, PrecursiveSyncResult


# Action Item Schemas
class ActionItemBase(BaseModel):
    """Base action item schema."""
    title: str
    status: ActionStatus = ActionStatus.TO_DO
    assignee: Optional[str] = None
    due_date: Optional[datetime] = None
    priority: Priority = Priority.MEDIUM
    jira_id: Optional[str] = None
    jira_key: Optional[str] = None
    issue_type: Optional[str] = None


class ActionItemCreate(ActionItemBase):
    """Schema for creating an action item."""
    project_id: uuid.UUID


class ActionItemRead(ActionItemBase):
    """Schema for reading action item data."""
    id: uuid.UUID
    project_id: uuid.UUID
    last_synced_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# Risk Schemas
class RiskBase(BaseModel):
    """Base risk schema."""
    title: str
    description: str
    category: Optional[str] = None
    impact_rationale: Optional[str] = None
    date_identified: Optional[datetime] = None
    probability: RiskProbability
    impact: RiskImpact
    status: RiskStatus = RiskStatus.OPEN
    mitigation_plan: Optional[str] = None


class RiskCreate(RiskBase):
    """Schema for creating a risk."""
    project_id: uuid.UUID


class RiskRead(RiskBase):
    """Schema for reading risk data."""
    id: uuid.UUID
    project_id: uuid.UUID
    
    class Config:
        from_attributes = True


__all__ = [
    # Auth
    "GoogleLoginRequest",
    "Token",
    # User
    "UserRead",
    "UserCreate",
    # Project
    "ProjectBase",
    "ProjectCreate",
    "ProjectRead",
    "ProjectUpdate",
    # Action Items
    "ActionItemBase",
    "ActionItemCreate",
    "ActionItemRead",
    # Risks
    "RiskBase",
    "RiskCreate",
    "RiskRead",
    # Sync
    "SyncResult",
    "SyncStatus",
    "JiraSyncResult",
    "PrecursiveSyncResult",
]
