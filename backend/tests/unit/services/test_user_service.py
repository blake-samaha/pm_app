"""Unit tests for UserService."""

import pytest

from exceptions import DuplicateResourceError
from models import AuthProvider, UserRole
from services.user_service import UserService


class TestDetermineRole:
    """Tests for the role determination business logic."""

    def test_cognite_email_gets_cogniter_role(self, session):
        """Users with @cognite.com email should be Cogniters."""
        service = UserService(session)

        role = service._determine_role("john.doe@cognite.com")

        assert role == UserRole.COGNITER

    def test_external_email_gets_client_role(self, session):
        """Users with non-cognite emails should be Clients."""
        service = UserService(session)

        role = service._determine_role("jane@acme.com")

        assert role == UserRole.CLIENT

    def test_subdomain_email_gets_client_role(self, session):
        """Subdomains of cognite.com should NOT be treated as Cogniters."""
        service = UserService(session)

        # This is a security test - subdomains shouldn't get elevated access
        role = service._determine_role("hacker@fake.cognite.com")

        assert role == UserRole.CLIENT


class TestGetOrCreateUser:
    """Tests for user creation and retrieval."""

    def test_creates_new_user_when_not_exists(self, session):
        """Should create a new user if email doesn't exist."""
        service = UserService(session)

        user, created = service.get_or_create_user(
            email="new.user@cognite.com",
            name="New User",
            auth_provider=AuthProvider.GOOGLE,
        )

        assert created is True
        assert user.email == "new.user@cognite.com"
        assert user.name == "New User"
        assert user.role == UserRole.COGNITER
        assert user.is_pending is False

    def test_returns_existing_user_without_creating(self, session, cogniter_user):
        """Should return existing user without creating a new one."""
        service = UserService(session)

        user, created = service.get_or_create_user(
            email=cogniter_user.email,
            name="Different Name",  # Should be ignored
            auth_provider=AuthProvider.GOOGLE,
        )

        assert created is False
        assert user.id == cogniter_user.id
        assert user.name == cogniter_user.name  # Original name preserved

    def test_activates_pending_user_on_registration(self, session, pending_user):
        """When a pending user registers, they should be activated."""
        service = UserService(session)

        user, created = service.get_or_create_user(
            email=pending_user.email,
            name="Real Name",
            auth_provider=AuthProvider.GOOGLE,
        )

        # Should return True because this is effectively a new registration
        assert created is True
        assert user.id == pending_user.id  # Same user record
        assert user.name == "Real Name"  # Name updated
        assert user.is_pending is False  # No longer pending
        assert user.auth_provider == AuthProvider.GOOGLE


class TestCreatePendingUser:
    """Tests for the invite/pending user flow."""

    def test_creates_pending_user(self, session):
        """Should create a placeholder user with is_pending=True."""
        service = UserService(session)

        user = service.create_pending_user("invited@external.com")

        assert user.email == "invited@external.com"
        assert user.is_pending is True
        assert user.name == "invited"  # Email prefix as placeholder
        assert user.role == UserRole.CLIENT

    def test_cognite_email_pending_user_gets_cogniter_role(self, session):
        """Even pending users should get correct role based on email."""
        service = UserService(session)

        user = service.create_pending_user("future.employee@cognite.com")

        assert user.role == UserRole.COGNITER

    def test_duplicate_email_raises_error(self, session, client_user):
        """Should raise DuplicateResourceError if email already exists."""
        service = UserService(session)

        with pytest.raises(DuplicateResourceError) as exc_info:
            service.create_pending_user(client_user.email)

        assert "already exists" in str(exc_info.value)


class TestSearchUsers:
    """Tests for user search functionality."""

    def test_search_by_name(self, session, cogniter_user, client_user):
        """Should find users by name substring."""
        service = UserService(session)

        results = service.search_users(search="Cogniter")

        assert len(results) == 1
        assert results[0].id == cogniter_user.id

    def test_search_by_email(self, session, cogniter_user, client_user):
        """Should find users by email substring."""
        service = UserService(session)

        results = service.search_users(search="acme")

        assert len(results) == 1
        assert results[0].id == client_user.id

    def test_filter_by_role(self, session, cogniter_user, client_user):
        """Should filter users by role."""
        service = UserService(session)

        results = service.search_users(role=UserRole.CLIENT)

        assert all(u.role == UserRole.CLIENT for u in results)
