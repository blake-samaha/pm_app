"""Project repository."""

from typing import List, Optional
from uuid import UUID

from sqlmodel import Session, select

from models import Project, User, UserProjectLink
from repositories.base import BaseRepository


class ProjectRepository(BaseRepository[Project]):
    """Repository for Project model with specialized queries."""

    def __init__(self, session: Session):
        super().__init__(Project, session)

    def get_by_precursive_url(self, url: str) -> Optional[Project]:
        """Get project by Precursive URL."""
        statement = select(Project).where(Project.precursive_url == url)
        return self.session.exec(statement).first()

    def get_published_projects(self) -> List[Project]:
        """Get all published projects."""
        statement = select(Project).where(Project.is_published)
        return list(self.session.exec(statement).all())

    def get_user_projects(self, user_id: UUID) -> List[Project]:
        """Get all projects assigned to a user."""
        statement = (
            select(Project)
            .join(UserProjectLink)
            .where(UserProjectLink.user_id == user_id)
        )
        return list(self.session.exec(statement).all())

    def add_user_to_project(self, project_id: UUID, user_id: UUID) -> None:
        """Assign a user to a project."""
        link = UserProjectLink(project_id=project_id, user_id=user_id)
        self.session.add(link)
        self.session.commit()

    def remove_user_from_project(self, project_id: UUID, user_id: UUID) -> None:
        """Remove a user from a project."""
        statement = select(UserProjectLink).where(
            UserProjectLink.project_id == project_id, UserProjectLink.user_id == user_id
        )
        link = self.session.exec(statement).first()
        if link:
            self.session.delete(link)
            self.session.commit()

    def user_has_access(self, project_id: UUID, user_id: UUID) -> bool:
        """Check if a user has access to a project."""
        statement = select(UserProjectLink).where(
            UserProjectLink.project_id == project_id, UserProjectLink.user_id == user_id
        )
        return self.session.exec(statement).first() is not None

    def get_project_users(self, project_id: UUID) -> List[User]:
        """Get all users assigned to a project."""
        statement = (
            select(User)
            .join(UserProjectLink)
            .where(UserProjectLink.project_id == project_id)
        )
        return list(self.session.exec(statement).all())

    def precursive_url_exists(self, url: str) -> bool:
        """Check if Precursive URL already exists."""
        return self.get_by_precursive_url(url) is not None
