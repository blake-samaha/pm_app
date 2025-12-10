"""Actions router."""
from fastapi import APIRouter, HTTPException
from sqlmodel import select
from typing import List
import uuid

from schemas import ActionItemCreate, ActionItemRead
from dependencies import SessionDep, CurrentUser
from models import ActionItem, Project, UserRole

router = APIRouter(
    prefix="/actions",
    tags=["actions"],
)


@router.get("/", response_model=List[ActionItemRead])
async def read_actions(
    project_id: uuid.UUID,
    session: SessionDep,
    current_user: CurrentUser
):
    """Get all actions for a project."""
    # Verify access to project
    project = session.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if current_user.role == UserRole.CLIENT and project not in current_user.projects:
        raise HTTPException(status_code=403, detail="Not authorized")

    statement = select(ActionItem).where(ActionItem.project_id == project_id)
    actions = session.exec(statement).all()
    return actions


@router.post("/", response_model=ActionItemRead)
async def create_action(
    action: ActionItemCreate,
    session: SessionDep,
    current_user: CurrentUser
):
    """Create a new action item."""
    # Verify access to project
    project = session.get(Project, action.project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if current_user.role == UserRole.CLIENT and project not in current_user.projects:
        raise HTTPException(status_code=403, detail="Not authorized")

    db_action = ActionItem.model_validate(action)
    session.add(db_action)
    session.commit()
    session.refresh(db_action)
    return db_action
