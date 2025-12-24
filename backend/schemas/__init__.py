"""Schemas package - exports all Pydantic schemas.

Response schemas (Read schemas) define field requiredness explicitly to ensure OpenAPI
accurately reflects the JSON response shape:
- Required non-null fields: no default, not Optional
- Required nullable fields: Optional[T] with no default (required in JSON but can be null)
"""

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict

from models import ActionStatus, Priority, RiskImpact, RiskProbability, RiskStatus
from schemas.auth import GoogleLoginRequest, SuperuserLoginRequest, Token
from schemas.project import ProjectBase, ProjectCreate, ProjectRead, ProjectUpdate
from schemas.sync import (
    JiraSyncResult,
    PrecursiveSyncResult,
    SyncJobEnqueued,
    SyncJobRead,
    SyncJobSummary,
    SyncResult,
    SyncStatus,
)
from schemas.user import (
    InviteUserRequest,
    InviteUserResponse,
    UserCreate,
    UserRead,
    UserRoleUpdate,
)


# Action Item Schemas
class ActionItemBase(BaseModel):
    """Base action item schema for creation. Has defaults for optional fields."""

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


class ActionItemRead(BaseModel):
    """Schema for reading action item data.

    All fields are explicitly defined to ensure OpenAPI required/nullable is accurate.
    """

    model_config = ConfigDict(from_attributes=True)

    # Always present, never null
    id: uuid.UUID
    project_id: uuid.UUID
    title: str
    status: ActionStatus
    priority: Priority
    comment_count: int

    # Always present in JSON, but can be null
    assignee: Optional[str]
    due_date: Optional[datetime]
    jira_id: Optional[str]
    jira_key: Optional[str]
    issue_type: Optional[str]
    last_synced_at: Optional[datetime]


class PaginatedActionsResponse(BaseModel):
    """Paginated response for action items."""

    items: list[ActionItemRead]
    total: int
    limit: int
    offset: int


# Risk Schemas
class RiskBase(BaseModel):
    """Base risk schema for creation. Has defaults for optional fields."""

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


class RiskRead(BaseModel):
    """Schema for reading risk data.

    All fields are explicitly defined to ensure OpenAPI required/nullable is accurate.
    """

    model_config = ConfigDict(from_attributes=True)

    # Always present, never null
    id: uuid.UUID
    project_id: uuid.UUID
    title: str
    description: str
    probability: RiskProbability
    impact: RiskImpact
    status: RiskStatus

    # Always present in JSON, but can be null
    category: Optional[str]
    impact_rationale: Optional[str]
    date_identified: Optional[datetime]
    mitigation_plan: Optional[str]

    # Resolution fields (null when not resolved)
    decision_record: Optional[str]
    resolved_at: Optional[datetime]
    resolved_by_id: Optional[uuid.UUID]

    # Reopen fields (null when not reopened)
    reopen_reason: Optional[str]
    reopened_at: Optional[datetime]
    reopened_by_id: Optional[uuid.UUID]


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
    """Schema for reading comment data.

    All fields are explicitly defined to ensure OpenAPI required/nullable is accurate.
    """

    model_config = ConfigDict(from_attributes=True)

    # Always present, never null
    id: uuid.UUID
    user_id: uuid.UUID
    content: str
    created_at: datetime

    # Always present in JSON, but can be null (only one will be set per comment)
    action_item_id: Optional[uuid.UUID]
    risk_id: Optional[uuid.UUID]

    # Author identity (populated from joined User)
    author_name: Optional[str]
    author_email: Optional[str]


__all__ = [
    # Auth
    "GoogleLoginRequest",
    "SuperuserLoginRequest",
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
    "PaginatedActionsResponse",
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
    "SyncJobRead",
    "SyncJobSummary",
    "SyncJobEnqueued",
]
