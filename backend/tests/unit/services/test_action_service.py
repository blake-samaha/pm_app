"""Unit tests for ActionService."""

from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from exceptions import AuthorizationError, ResourceNotFoundError
from models import ActionItem, ActionStatus, AuthProvider, Priority, User, UserRole
from services.action_service import ActionService


@pytest.fixture
def mock_session():
    """Create a mock database session."""
    session = MagicMock()
    return session


@pytest.fixture
def cogniter_user():
    """Create a Cogniter user for testing."""
    return User(
        id=uuid4(),
        email="pm@cognite.com",
        name="PM User",
        role=UserRole.COGNITER,
        auth_provider=AuthProvider.GOOGLE,
        is_pending=False,
    )


@pytest.fixture
def client_user():
    """Create a Client user for testing."""
    return User(
        id=uuid4(),
        email="client@acme.com",
        name="Client User",
        role=UserRole.CLIENT,
        auth_provider=AuthProvider.EMAIL,
        is_pending=False,
    )


@pytest.fixture
def sample_action():
    """Create a sample action item for testing."""
    return ActionItem(
        id=uuid4(),
        project_id=uuid4(),
        title="Test Action",
        status=ActionStatus.TO_DO,
        priority=Priority.MEDIUM,
    )


@pytest.fixture
def sample_project():
    """Create a sample project for testing."""
    project = MagicMock()
    project.id = uuid4()
    return project


class TestActionService:
    """Tests for ActionService."""

    def test_get_project_actions_respects_access_control(
        self, mock_session, client_user, sample_action, sample_project
    ):
        """Client should not see actions for unassigned projects."""
        service = ActionService(mock_session)

        with patch.object(
            service.project_repository, "get_by_id", return_value=sample_project
        ):
            with patch.object(
                service.project_repository, "user_has_access", return_value=False
            ):
                with pytest.raises(AuthorizationError) as exc_info:
                    service.get_project_actions(sample_project.id, client_user)

                assert "don't have access" in str(exc_info.value)

    def test_cogniter_can_access_any_project_actions(
        self, mock_session, cogniter_user, sample_action, sample_project
    ):
        """Cogniters should be able to access actions for any project."""
        service = ActionService(mock_session)

        with patch.object(
            service.project_repository, "get_by_id", return_value=sample_project
        ):
            with patch.object(
                service.repository, "get_by_project", return_value=[sample_action]
            ):
                # Cogniters bypass the user_has_access check
                result = service.get_project_actions(sample_project.id, cogniter_user)
                assert result == [sample_action]

    def test_client_can_access_assigned_project_actions(
        self, mock_session, client_user, sample_action, sample_project
    ):
        """Clients should be able to access actions for assigned projects."""
        service = ActionService(mock_session)

        with patch.object(
            service.project_repository, "get_by_id", return_value=sample_project
        ):
            with patch.object(
                service.project_repository, "user_has_access", return_value=True
            ):
                with patch.object(
                    service.repository, "get_by_project", return_value=[sample_action]
                ):
                    result = service.get_project_actions(sample_project.id, client_user)
                    assert result == [sample_action]

    def test_create_action_requires_project_access(
        self, mock_session, client_user, sample_project
    ):
        """Creating an action requires project access."""
        service = ActionService(mock_session)

        create_data = MagicMock()
        create_data.project_id = sample_project.id

        with patch.object(
            service.project_repository, "get_by_id", return_value=sample_project
        ):
            with patch.object(
                service.project_repository, "user_has_access", return_value=False
            ):
                with pytest.raises(AuthorizationError):
                    service.create_action(create_data, client_user)

    def test_create_action_project_must_exist(self, mock_session, cogniter_user):
        """Creating an action requires project to exist."""
        service = ActionService(mock_session)

        create_data = MagicMock()
        create_data.project_id = uuid4()

        with patch.object(service.project_repository, "get_by_id", return_value=None):
            with pytest.raises(ResourceNotFoundError):
                service.create_action(create_data, cogniter_user)

    def test_delete_action_requires_cogniter(
        self, mock_session, client_user, sample_action
    ):
        """Only Cogniters can delete actions."""
        service = ActionService(mock_session)

        with patch.object(service.repository, "get_by_id", return_value=sample_action):
            with pytest.raises(AuthorizationError) as exc_info:
                service.delete_action(sample_action.id, client_user)

            assert "Only Cogniters" in str(exc_info.value)

    def test_cogniter_can_delete_action(
        self, mock_session, cogniter_user, sample_action
    ):
        """Cogniters should be able to delete actions."""
        service = ActionService(mock_session)

        with patch.object(service.repository, "get_by_id", return_value=sample_action):
            with patch.object(service.repository, "delete", return_value=True):
                result = service.delete_action(sample_action.id, cogniter_user)
                assert result is True

    def test_get_by_jira_key(self, mock_session, sample_action):
        """Should be able to lookup action by Jira key."""
        service = ActionService(mock_session)
        sample_action.jira_key = "PROJ-123"

        with patch.object(
            service.repository, "get_by_jira_key", return_value=sample_action
        ):
            result = service.get_by_jira_key("PROJ-123")
            assert result is not None
            assert result == sample_action
            assert result.jira_key == "PROJ-123"

    def test_get_by_jira_id(self, mock_session, sample_action):
        """Should be able to lookup action by Jira internal ID."""
        service = ActionService(mock_session)
        sample_action.jira_id = "12345"

        with patch.object(
            service.repository, "get_by_jira_id", return_value=sample_action
        ):
            result = service.get_by_jira_id("12345")
            assert result == sample_action


class TestActionServiceComments:
    """Tests for ActionService comment functionality."""

    def test_client_can_comment_on_assigned_project(
        self, mock_session, client_user, sample_action, sample_project
    ):
        """Clients can comment on actions for projects they're assigned to."""
        service = ActionService(mock_session)
        sample_action.project_id = sample_project.id
        sample_project.is_published = True

        with patch.object(service.repository, "get_by_id", return_value=sample_action):
            with patch.object(
                service.project_repository, "get_by_id", return_value=sample_project
            ):
                with patch.object(
                    service.project_repository, "user_has_access", return_value=True
                ):
                    with patch.object(service.comment_repository, "create"):
                        # Should not raise
                        _ = service.add_comment(
                            sample_action.id, "Test comment", client_user
                        )

    def test_client_cannot_comment_on_unassigned_project(
        self, mock_session, client_user, sample_action, sample_project
    ):
        """Clients cannot comment on actions for unassigned projects."""
        service = ActionService(mock_session)
        sample_action.project_id = sample_project.id

        with patch.object(service.repository, "get_by_id", return_value=sample_action):
            with patch.object(
                service.project_repository, "get_by_id", return_value=sample_project
            ):
                with patch.object(
                    service.project_repository, "user_has_access", return_value=False
                ):
                    with pytest.raises(AuthorizationError):
                        service.add_comment(
                            sample_action.id, "Test comment", client_user
                        )

    def test_cogniter_can_comment_on_any_project(
        self, mock_session, cogniter_user, sample_action
    ):
        """Cogniters can comment on any action."""
        service = ActionService(mock_session)

        with patch.object(service.repository, "get_by_id", return_value=sample_action):
            with patch.object(service.comment_repository, "create"):
                # Should not raise - Cogniters bypass project access check
                _ = service.add_comment(sample_action.id, "PM comment", cogniter_user)

    def test_empty_comment_rejected(self, mock_session, cogniter_user, sample_action):
        """Empty comments should be rejected."""
        from exceptions import ValidationError

        service = ActionService(mock_session)

        with patch.object(service.repository, "get_by_id", return_value=sample_action):
            with pytest.raises(ValidationError):
                service.add_comment(sample_action.id, "", cogniter_user)

    def test_whitespace_comment_rejected(
        self, mock_session, cogniter_user, sample_action
    ):
        """Whitespace-only comments should be rejected."""
        from exceptions import ValidationError

        service = ActionService(mock_session)

        with patch.object(service.repository, "get_by_id", return_value=sample_action):
            with pytest.raises(ValidationError):
                service.add_comment(sample_action.id, "   ", cogniter_user)

    def test_get_comments_requires_project_access(
        self, mock_session, client_user, sample_action, sample_project
    ):
        """Getting comments requires project access."""
        service = ActionService(mock_session)
        sample_action.project_id = sample_project.id

        with patch.object(service.repository, "get_by_id", return_value=sample_action):
            with patch.object(
                service.project_repository, "get_by_id", return_value=sample_project
            ):
                with patch.object(
                    service.project_repository, "user_has_access", return_value=False
                ):
                    with pytest.raises(AuthorizationError):
                        service.get_comments(sample_action.id, client_user)

    def test_comment_returns_author_info(
        self, mock_session, cogniter_user, sample_action
    ):
        """Added comment should include author information."""
        from models import Comment

        service = ActionService(mock_session)
        mock_comment = Comment(
            id=uuid4(),
            action_item_id=sample_action.id,
            user_id=cogniter_user.id,
            content="Test comment",
        )

        with patch.object(service.repository, "get_by_id", return_value=sample_action):
            with patch.object(
                service.comment_repository, "create", return_value=mock_comment
            ):
                comment, author = service.add_comment(
                    sample_action.id, "Test comment", cogniter_user
                )
                assert comment == mock_comment
                assert author == cogniter_user
