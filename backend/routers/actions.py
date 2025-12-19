"""Actions router."""

import uuid
from typing import List

from fastapi import APIRouter, HTTPException, status

from dependencies import ActionServiceDep, CogniterUser, CurrentUser
from exceptions import AuthorizationError, ResourceNotFoundError, ValidationError
from schemas import ActionItemCreate, ActionItemRead, CommentCreate, CommentRead
from serializers.api_models import to_action_item_read, to_comment_read

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
        rows = action_service.get_project_actions_with_comment_counts(
            project_id, current_user
        )
        return [
            to_action_item_read(action, comment_count) for action, comment_count in rows
        ]
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


# =============================================================================
# Comment Endpoints
# =============================================================================


@router.get("/{action_id}/comments", response_model=List[CommentRead])
async def get_action_comments(
    action_id: uuid.UUID, current_user: CurrentUser, action_service: ActionServiceDep
):
    """
    Get all comments for an action item.

    Both Cogniters and assigned Clients can view comments.
    """
    try:
        rows = action_service.get_comments(action_id, current_user)
        return [to_comment_read(comment, author) for comment, author in rows]
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except AuthorizationError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.post(
    "/{action_id}/comments",
    response_model=CommentRead,
    status_code=status.HTTP_201_CREATED,
)
async def add_action_comment(
    action_id: uuid.UUID,
    data: CommentCreate,
    current_user: CurrentUser,
    action_service: ActionServiceDep,
):
    """
    Add a comment to an action item.

    Both Cogniters and assigned Clients can comment on actions.
    """
    try:
        comment, author = action_service.add_comment(
            action_id, data.content, current_user
        )
        return to_comment_read(comment, author)
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except AuthorizationError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(e)
        )
