"""Seed stable QA personas (and optionally a sandbox project) for local QA.

Usage (from backend/):
    uv run python -m scripts.seed_qa_personas --create-sandbox-project
"""

from __future__ import annotations

import argparse

from sqlmodel import Session, select

from database import engine
from models import Project, UserRole
from models.links import UserProjectLink
from models.project import ProjectType
from services.user_service import UserService

QA_SANDBOX_PROJECT_NAME = "QA Sandbox Project"


def _ensure_sandbox_project(session: Session) -> Project:
    existing = session.exec(
        select(Project).where(Project.name == QA_SANDBOX_PROJECT_NAME)
    ).first()
    if existing:
        # Ensure it's published so client personas can see it.
        if not existing.is_published:
            existing.is_published = True
            session.add(existing)
            session.commit()
            session.refresh(existing)
        return existing

    project = Project(
        name=QA_SANDBOX_PROJECT_NAME,
        type=ProjectType.FIXED_PRICE,
        precursive_url="https://example.com/precursive/qa-sandbox",
        jira_url="https://example.com/jira/qa-sandbox",
        is_published=True,
    )
    session.add(project)
    session.commit()
    session.refresh(project)
    return project


def _assign_user_to_project(session: Session, project_id, user_id) -> None:
    existing_link = session.exec(
        select(UserProjectLink).where(
            UserProjectLink.project_id == project_id, UserProjectLink.user_id == user_id
        )
    ).first()
    if existing_link:
        return
    session.add(UserProjectLink(project_id=project_id, user_id=user_id))
    session.commit()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Seed QA personas for impersonation testing."
    )
    parser.add_argument(
        "--create-sandbox-project",
        action="store_true",
        help="Create a published QA Sandbox Project and assign client personas to it.",
    )
    args = parser.parse_args()

    with Session(engine) as session:
        user_service = UserService(session)
        users = user_service.ensure_qa_personas()

        print("Ensured QA personas:")
        for user in users:
            print(f"- {user.name} ({user.email}) role={user.role}")

        if args.create_sandbox_project:
            project = _ensure_sandbox_project(session)
            print(f"\nEnsured sandbox project: {project.name} (id={project.id})")

            for user in users:
                if user.role in (UserRole.CLIENT, UserRole.CLIENT_FINANCIALS):
                    _assign_user_to_project(session, project.id, user.id)
                    print(f"- Assigned {user.email} -> {project.name}")


if __name__ == "__main__":
    main()
