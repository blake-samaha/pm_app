"""Schemas package - exports all Pydantic schemas."""

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from models import ActionStatus, Priority, RiskImpact, RiskProbability, RiskStatus
from schemas.auth import GoogleLoginRequest, Token
from schemas.project import ProjectBase, ProjectCreate, ProjectRead, ProjectUpdate
from schemas.sync import JiraSyncResult, PrecursiveSyncResult, SyncResult, SyncStatus
from schemas.user import (
    InviteUserRequest,
    InviteUserResponse,
    UserCreate,
    UserRead,
    UserRoleUpdate,
)


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
    # Resolution fields
    decision_record: Optional[str] = None
    resolved_at: Optional[datetime] = None
    resolved_by_id: Optional[uuid.UUID] = None
    # Reopen fields
    reopen_reason: Optional[str] = None
    reopened_at: Optional[datetime] = None
    reopened_by_id: Optional[uuid.UUID] = None

    class Config:
        from_attributes = True


class RiskResolve(BaseModel):
    """Schema for resolving a risk."""

    status: RiskStatus  # Must be CLOSED or MITIGATED
    decision_record: str  # Required, non-empty


class RiskReopen(BaseModel):
    """Schema for reopening a resolved risk."""

    reason: str  # Required explanation for reopening


class RiskUpdate(BaseModel):
    """Schema for updating a risk."""

    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    impact_rationale: Optional[str] = None
    probability: Optional[RiskProbability] = None
    impact: Optional[RiskImpact] = None
    mitigation_plan: Optional[str] = None


# Comment Schemas
class CommentCreate(BaseModel):
    """Schema for creating a comment."""

    content: str


class CommentRead(BaseModel):
    """Schema for reading comment data."""

    id: uuid.UUID
    user_id: uuid.UUID
    content: str
    created_at: datetime
    action_item_id: Optional[uuid.UUID] = None
    risk_id: Optional[uuid.UUID] = None

    class Config:
        from_attributes = True


__all__ = [
    # Auth
    "GoogleLoginRequest",
    "Token",
    # User
    "UserRead",
    "UserCreate",
    "UserRoleUpdate",
    "InviteUserRequest",
    "InviteUserResponse",
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
    "RiskResolve",
    "RiskReopen",
    "RiskUpdate",
    # Comments
    "CommentCreate",
    "CommentRead",
    # Sync
    "SyncResult",
    "SyncStatus",
    "JiraSyncResult",
    "PrecursiveSyncResult",
]
