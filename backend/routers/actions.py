"""Actions router."""

import uuid
from typing import List

from fastapi import APIRouter, HTTPException, status

from dependencies import ActionServiceDep, CogniterUser, CurrentUser
from exceptions import AuthorizationError, ResourceNotFoundError
from schemas import ActionItemCreate, ActionItemRead

router = APIRouter(
    prefix="/actions",
    tags=["actions"],
)


@router.get("/", response_model=List[ActionItemRead])
async def read_actions(
    project_id: uuid.UUID, current_user: CurrentUser, action_service: ActionServiceDep
):
    """Get all actions for a project."""
    try:
        return action_service.get_project_actions(project_id, current_user)
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except AuthorizationError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.post("/", response_model=ActionItemRead, status_code=status.HTTP_201_CREATED)
async def create_action(
    action: ActionItemCreate,
    current_user: CurrentUser,
    action_service: ActionServiceDep,
):
    """Create a new action item."""
    try:
        return action_service.create_action(action, current_user)
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except AuthorizationError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.get("/{action_id}", response_model=ActionItemRead)
async def get_action(
    action_id: uuid.UUID, current_user: CurrentUser, action_service: ActionServiceDep
):
    """Get a specific action item by ID."""
    try:
        action = action_service.get_action_by_id(action_id)
        # Check project access
        action_service._check_project_access(action.project_id, current_user)
        return action
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except AuthorizationError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.delete("/{action_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_action(
    action_id: uuid.UUID,
    current_user: CogniterUser,  # Only Cogniters can delete
    action_service: ActionServiceDep,
):
    """Delete an action item. Only Cogniters can delete actions."""
    try:
        action_service.delete_action(action_id, current_user)
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except AuthorizationError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
