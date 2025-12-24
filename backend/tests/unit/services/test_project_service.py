"""Unit tests for ProjectService."""

from uuid import uuid4

import pytest

from exceptions import AuthorizationError, DuplicateResourceError
from models import AuthProvider, User, UserRole
from models.project import ProjectType
from schemas.project import ProjectCreate, ProjectUpdate
from services.project_service import ProjectService


class TestCreateProject:
    """Tests for project creation authorization."""

    def test_cogniter_can_create_project(self, session, cogniter_user):
        """Cogniters should be able to create projects."""
        service = ProjectService(session)
        project_data = ProjectCreate(
            name="New Project",
            type=ProjectType.FIXED_PRICE,
            precursive_url="https://precursive.example.com/new",
            jira_url="https://jira.example.com/projects/NEW",
        )

        project = service.create_project(project_data, cogniter_user)

        assert project.name == "New Project"
        assert project.id is not None

    def test_client_cannot_create_project(self, session, client_user):
        """Clients should NOT be able to create projects."""
        service = ProjectService(session)
        project_data = ProjectCreate(
            name="New Project",
            type=ProjectType.FIXED_PRICE,
            precursive_url="https://precursive.example.com/new",
            jira_url="https://jira.example.com/projects/NEW",
        )

        with pytest.raises(AuthorizationError) as exc_info:
            service.create_project(project_data, client_user)

        assert "Only Cogniters" in str(exc_info.value)

    def test_duplicate_precursive_url_rejected(
        self, session, cogniter_user, sample_project
    ):
        """Should reject projects with duplicate Precursive URLs."""
        service = ProjectService(session)
        project_data = ProjectCreate(
            name="Duplicate Project",
            type=ProjectType.FIXED_PRICE,
            precursive_url=sample_project.precursive_url,  # Same URL
            jira_url="https://jira.example.com/projects/DUP",
        )

        with pytest.raises(DuplicateResourceError):
            service.create_project(project_data, cogniter_user)


class TestGetUserProjects:
    """Tests for project visibility based on user role."""

    def test_cogniter_sees_all_projects(self, session, cogniter_user, sample_project):
        """Cogniters should see all projects."""
        service = ProjectService(session)

        projects = service.get_user_projects(cogniter_user)

        assert len(projects) >= 1
        assert sample_project.id in [p.id for p in projects]

    def test_client_sees_only_assigned_projects(
        self, session, client_user, sample_project
    ):
        """Clients should only see projects they're assigned to."""
        service = ProjectService(session)

        # Initially, client has no projects
        projects = service.get_user_projects(client_user)
        assert len(projects) == 0

        # Assign client to project (using a Cogniter to do the assignment)
        cogniter = User(
            id=uuid4(),
            email="admin@cognite.com",
            name="Admin",
            role=UserRole.COGNITER,
            auth_provider=AuthProvider.GOOGLE,
        )
        session.add(cogniter)
        session.commit()

        service.assign_user_to_project(sample_project.id, client_user.id, cogniter)

        # Clients only see projects once they're published
        service.publish_project(sample_project.id, cogniter)

        # Now client should see the published project
        projects = service.get_user_projects(client_user)
        assert len(projects) == 1
        assert projects[0].id == sample_project.id


class TestProjectAuthorization:
    """Tests for project modification authorization."""

    def test_cogniter_can_update_project(self, session, cogniter_user, sample_project):
        """Cogniters should be able to update projects."""
        service = ProjectService(session)
        update_data = ProjectUpdate(name="Updated Name")

        updated = service.update_project(sample_project.id, update_data, cogniter_user)

        assert updated.name == "Updated Name"

    def test_client_cannot_update_project(self, session, client_user, sample_project):
        """Clients should NOT be able to update projects."""
        service = ProjectService(session)
        update_data = ProjectUpdate(name="Hacked Name")

        with pytest.raises(AuthorizationError):
            service.update_project(sample_project.id, update_data, client_user)

    def test_cogniter_can_publish_project(self, session, cogniter_user, sample_project):
        """Cogniters should be able to publish projects."""
        service = ProjectService(session)

        published = service.publish_project(sample_project.id, cogniter_user)

        assert published.is_published is True

    def test_client_cannot_publish_project(self, session, client_user, sample_project):
        """Clients should NOT be able to publish projects."""
        service = ProjectService(session)

        with pytest.raises(AuthorizationError):
            service.publish_project(sample_project.id, client_user)


class TestUserAssignment:
    """Tests for assigning users to projects."""

    def test_cogniter_can_assign_user(
        self, session, cogniter_user, client_user, sample_project
    ):
        """Cogniters should be able to assign users to projects."""
        service = ProjectService(session)

        # Should not raise
        service.assign_user_to_project(sample_project.id, client_user.id, cogniter_user)

        # Verify assignment
        users = service.get_project_users(sample_project.id)
        assert client_user.id in [u.id for u in users]

    def test_client_cannot_assign_user(self, session, client_user, sample_project):
        """Clients should NOT be able to assign users."""
        service = ProjectService(session)

        another_user = User(
            id=uuid4(),
            email="other@example.com",
            name="Other",
            role=UserRole.CLIENT,
            auth_provider=AuthProvider.GOOGLE,
        )
        session.add(another_user)
        session.commit()

        with pytest.raises(AuthorizationError):
            service.assign_user_to_project(
                sample_project.id,
                another_user.id,
                client_user,  # Client trying to assign
            )


class TestAccessControl:
    """Tests for project access checking."""

    def test_cogniter_has_access_to_all_projects(
        self, session, cogniter_user, sample_project
    ):
        """Cogniters should have access to all projects."""
        service = ProjectService(session)

        has_access = service.user_has_access_to_project(
            sample_project.id, cogniter_user
        )

        assert has_access is True

    def test_unassigned_client_has_no_access(
        self, session, client_user, sample_project
    ):
        """Clients should NOT have access to unassigned projects."""
        service = ProjectService(session)

        has_access = service.user_has_access_to_project(sample_project.id, client_user)

        assert has_access is False
