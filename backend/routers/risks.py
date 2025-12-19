"""Risks router."""

import uuid
from typing import List

from fastapi import APIRouter, HTTPException, status

from dependencies import CogniterUser, CurrentUser, RiskServiceDep
from exceptions import AuthorizationError, ResourceNotFoundError, ValidationError
from schemas import (
    CommentCreate,
    CommentRead,
    RiskCreate,
    RiskRead,
    RiskReopen,
    RiskResolve,
)
from serializers.api_models import to_comment_read

router = APIRouter(
    prefix="/risks",
    tags=["risks"],
)


@router.get("/", response_model=List[RiskRead])
async def read_risks(
    project_id: uuid.UUID, current_user: CurrentUser, risk_service: RiskServiceDep
):
    """Get all risks for a project."""
    try:
        return risk_service.get_project_risks(project_id, current_user)
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except AuthorizationError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.post("/", response_model=RiskRead, status_code=status.HTTP_201_CREATED)
async def create_risk(
    risk: RiskCreate, current_user: CurrentUser, risk_service: RiskServiceDep
):
    """Create a new risk."""
    try:
        return risk_service.create_risk(risk, current_user)
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except AuthorizationError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.get("/{risk_id}", response_model=RiskRead)
async def get_risk(
    risk_id: uuid.UUID, current_user: CurrentUser, risk_service: RiskServiceDep
):
    """Get a specific risk by ID."""
    try:
        risk = risk_service.get_risk_by_id(risk_id)
        # Check project access
        risk_service._check_project_access(risk.project_id, current_user)
        return risk
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except AuthorizationError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.post("/{risk_id}/resolve", response_model=RiskRead)
async def resolve_risk(
    risk_id: uuid.UUID,
    data: RiskResolve,
    current_user: CogniterUser,  # Only Cogniters can resolve
    risk_service: RiskServiceDep,
):
    """
    Resolve a risk with a decision record.

    - Only Cogniters can resolve risks
    - Status must be CLOSED or MITIGATED
    - Decision record is required
    """
    try:
        return risk_service.resolve_risk(
            risk_id=risk_id,
            status=data.status,
            decision_record=data.decision_record,
            user=current_user,
        )
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except AuthorizationError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(e)
        )


@router.post("/{risk_id}/reopen", response_model=RiskRead)
async def reopen_risk(
    risk_id: uuid.UUID,
    data: RiskReopen,
    current_user: CogniterUser,  # Only Cogniters can reopen
    risk_service: RiskServiceDep,
):
    """
    Reopen a previously resolved risk.

    - Only Cogniters can reopen risks
    - Reason is required
    """
    try:
        return risk_service.reopen_risk(
            risk_id=risk_id, reason=data.reason, user=current_user
        )
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except AuthorizationError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(e)
        )


@router.get("/{risk_id}/comments", response_model=List[CommentRead])
async def get_risk_comments(
    risk_id: uuid.UUID, current_user: CurrentUser, risk_service: RiskServiceDep
):
    """
    Get all comments for a risk.

    Both Cogniters and assigned Clients can view comments.
    """
    try:
        rows = risk_service.get_comments(risk_id, current_user)
        return [to_comment_read(comment, author) for comment, author in rows]
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except AuthorizationError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.post(
    "/{risk_id}/comments",
    response_model=CommentRead,
    status_code=status.HTTP_201_CREATED,
)
async def add_risk_comment(
    risk_id: uuid.UUID,
    data: CommentCreate,
    current_user: CurrentUser,
    risk_service: RiskServiceDep,
):
    """
    Add a comment to a risk.

    Both Cogniters and assigned Clients can comment on risks.
    """
    try:
        comment, author = risk_service.add_comment(risk_id, data.content, current_user)
        return to_comment_read(comment, author)
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except AuthorizationError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(e)
        )


@router.delete("/{risk_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_risk(
    risk_id: uuid.UUID,
    current_user: CogniterUser,  # Only Cogniters can delete
    risk_service: RiskServiceDep,
):
    """Delete a risk. Only Cogniters can delete risks."""
    try:
        risk_service.delete_risk(risk_id, current_user)
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except AuthorizationError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
