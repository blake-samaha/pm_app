"""Unit tests for permissions module - TDD: Write first, implement second."""

from uuid import uuid4

import pytest

from models import AuthProvider, User, UserRole

# These imports will fail initially - that's expected in TDD
from permissions import (
    can_create_project,
    can_edit_project,
    can_manage_team,
    can_view_financials,
    is_client_role,
    is_internal_user,
)


@pytest.fixture
def cogniter():
    """Create a Cogniter user for permission tests."""
    return User(
        id=uuid4(),
        email="test@cognite.com",
        name="Test Cogniter",
        role=UserRole.COGNITER,
        auth_provider=AuthProvider.GOOGLE,
    )


@pytest.fixture
def client_financials():
    """Create a Client + Financials user for permission tests."""
    return User(
        id=uuid4(),
        email="senior@acme.com",
        name="Senior Client",
        role=UserRole.CLIENT_FINANCIALS,
        auth_provider=AuthProvider.GOOGLE,
    )


@pytest.fixture
def client():
    """Create a Client user for permission tests."""
    return User(
        id=uuid4(),
        email="client@acme.com",
        name="Client User",
        role=UserRole.CLIENT,
        auth_provider=AuthProvider.GOOGLE,
    )


class TestIsInternalUser:
    """Tests for is_internal_user permission check."""

    def test_cogniter_is_internal(self, cogniter):
        """Cogniter role should be considered internal."""
        assert is_internal_user(cogniter) is True

    def test_client_financials_not_internal(self, client_financials):
        """Client + Financials role should not be considered internal."""
        assert is_internal_user(client_financials) is False

    def test_client_not_internal(self, client):
        """Client role should not be considered internal."""
        assert is_internal_user(client) is False


class TestIsClientRole:
    """Tests for is_client_role permission check."""

    def test_cogniter_not_client_role(self, cogniter):
        """Cogniter should not be a client role."""
        assert is_client_role(cogniter) is False

    def test_client_financials_is_client_role(self, client_financials):
        """Client + Financials should be a client role."""
        assert is_client_role(client_financials) is True

    def test_client_is_client_role(self, client):
        """Client should be a client role."""
        assert is_client_role(client) is True


class TestCanViewFinancials:
    """Tests for can_view_financials permission check."""

    def test_cogniter_can_view(self, cogniter):
        """Cogniter should be able to view financials."""
        assert can_view_financials(cogniter) is True

    def test_client_financials_can_view(self, client_financials):
        """Client + Financials should be able to view financials."""
        assert can_view_financials(client_financials) is True

    def test_client_cannot_view(self, client):
        """Regular Client should not be able to view financials."""
        assert can_view_financials(client) is False


class TestCanManageTeam:
    """Tests for can_manage_team permission check."""

    def test_cogniter_can_manage(self, cogniter):
        """Cogniter should be able to manage team."""
        assert can_manage_team(cogniter) is True

    def test_client_financials_cannot_manage(self, client_financials):
        """Client + Financials should not be able to manage team."""
        assert can_manage_team(client_financials) is False

    def test_client_cannot_manage(self, client):
        """Client should not be able to manage team."""
        assert can_manage_team(client) is False


class TestCanEditProject:
    """Tests for can_edit_project permission check."""

    def test_cogniter_can_edit(self, cogniter):
        """Cogniter should be able to edit projects."""
        assert can_edit_project(cogniter) is True

    def test_client_financials_cannot_edit(self, client_financials):
        """Client + Financials should not be able to edit projects."""
        assert can_edit_project(client_financials) is False

    def test_client_cannot_edit(self, client):
        """Client should not be able to edit projects."""
        assert can_edit_project(client) is False


class TestCanCreateProject:
    """Tests for can_create_project permission check."""

    def test_cogniter_can_create(self, cogniter):
        """Cogniter should be able to create projects."""
        assert can_create_project(cogniter) is True

    def test_client_financials_cannot_create(self, client_financials):
        """Client + Financials should not be able to create projects."""
        assert can_create_project(client_financials) is False

    def test_client_cannot_create(self, client):
        """Client should not be able to create projects."""
        assert can_create_project(client) is False
