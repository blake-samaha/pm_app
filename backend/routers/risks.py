"""Risks router."""
from fastapi import APIRouter, HTTPException
from sqlmodel import select
from typing import List
import uuid

from schemas import RiskCreate, RiskRead
from dependencies import SessionDep, CurrentUser
from models import Risk, Project, UserRole

router = APIRouter(
    prefix="/risks",
    tags=["risks"],
)


@router.get("/", response_model=List[RiskRead])
async def read_risks(
    project_id: uuid.UUID,
    session: SessionDep,
    current_user: CurrentUser
):
    """Get all risks for a project."""
    # Verify access to project
    project = session.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if current_user.role == UserRole.CLIENT and project not in current_user.projects:
        raise HTTPException(status_code=403, detail="Not authorized")

    statement = select(Risk).where(Risk.project_id == project_id)
    risks = session.exec(statement).all()
    return risks


@router.post("/", response_model=RiskRead)
async def create_risk(
    risk: RiskCreate,
    session: SessionDep,
    current_user: CurrentUser
):
    """Create a new risk."""
    # Verify access to project
    project = session.get(Project, risk.project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if current_user.role == UserRole.CLIENT and project not in current_user.projects:
        raise HTTPException(status_code=403, detail="Not authorized")

    db_risk = Risk.model_validate(risk)
    session.add(db_risk)
    session.commit()
    session.refresh(db_risk)
    return db_risk
