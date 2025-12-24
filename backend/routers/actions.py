"""Actions router."""

import uuid
from typing import List, Optional, Union

from fastapi import APIRouter, Query, Response, status

from dependencies import ActionServiceDep, CogniterUser, CurrentUser
from schemas import (
    ActionItemCreate,
    ActionItemRead,
    CommentCreate,
    CommentRead,
    PaginatedActionsResponse,
)
from serializers.api_models import to_action_item_read, to_comment_read

router = APIRouter(
    prefix="/actions",
    tags=["actions"],
)


@router.get("/", response_model=Union[List[ActionItemRead], PaginatedActionsResponse])
async def read_actions(
    response: Response,
    project_id: uuid.UUID,
    current_user: CurrentUser,
    action_service: ActionServiceDep,
    limit: Optional[int] = Query(None, ge=1, le=100, description="Max items per page"),
    offset: Optional[int] = Query(None, ge=0, description="Number of items to skip"),
    search: Optional[str] = Query(None, description="Search in title or Jira ID"),
    status_filter: Optional[List[str]] = Query(
        None, alias="status", description="Filter by status"
    ),
):
    """
    Get actions for a project.

    If limit/offset are provided, returns paginated response with total count.
    Otherwise returns all actions (legacy behavior) with X-Total-Count header.

    - **limit**: Maximum number of results (1-100)
    - **offset**: Number of results to skip
    - **search**: Optional search term for title or Jira ID
    - **status**: Optional status filter (can be repeated)
    """
    # ResourceNotFoundError -> 404, AuthorizationError -> 403 via global handlers

    # If pagination params provided, use paginated method
    if limit is not None:
        effective_offset = offset if offset is not None else 0
        rows, total = action_service.get_project_actions_paginated(
            project_id=project_id,
            user=current_user,
            limit=limit,
            offset=effective_offset,
            search=search,
            statuses=status_filter,
        )
        items = [
            to_action_item_read(action, comment_count) for action, comment_count in rows
        ]
        return PaginatedActionsResponse(
            items=items,
            total=total,
            limit=limit,
            offset=effective_offset,
        )

    # Legacy behavior: return all actions as list
    rows = action_service.get_project_actions_with_comment_counts(
        project_id, current_user
    )
    items = [
        to_action_item_read(action, comment_count) for action, comment_count in rows
    ]
    # Add total count header for clients that want it
    response.headers["X-Total-Count"] = str(len(items))
    return items


@router.post("/", response_model=ActionItemRead, status_code=status.HTTP_201_CREATED)
async def create_action(
    action: ActionItemCreate,
    current_user: CurrentUser,
    action_service: ActionServiceDep,
):
    """Create a new action item."""
    # ResourceNotFoundError -> 404, AuthorizationError -> 403 via global handlers
    created = action_service.create_action(action, current_user)
    return to_action_item_read(created, comment_count=0)


@router.get("/{action_id}", response_model=ActionItemRead)
async def get_action(
    action_id: uuid.UUID, current_user: CurrentUser, action_service: ActionServiceDep
):
    """Get a specific action item by ID."""
    # ResourceNotFoundError -> 404, AuthorizationError -> 403 via global handlers
    action, comment_count = action_service.get_action_with_comment_count(
        action_id, current_user
    )
    return to_action_item_read(action, comment_count)


@router.delete("/{action_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_action(
    action_id: uuid.UUID,
    current_user: CogniterUser,  # Only Cogniters can delete
    action_service: ActionServiceDep,
):
    """Delete an action item. Only Cogniters can delete actions."""
    # ResourceNotFoundError -> 404, AuthorizationError -> 403 via global handlers
    action_service.delete_action(action_id, current_user)


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
    # ResourceNotFoundError -> 404, AuthorizationError -> 403 via global handlers
    rows = action_service.get_comments(action_id, current_user)
    return [to_comment_read(comment, author) for comment, author in rows]


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
    # ResourceNotFoundError -> 404, AuthorizationError -> 403,
    # ValidationError -> 400 via global handlers
    comment, author = action_service.add_comment(action_id, data.content, current_user)
    return to_comment_read(comment, author)
