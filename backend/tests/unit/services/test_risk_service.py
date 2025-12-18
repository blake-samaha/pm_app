"""Unit tests for RiskService."""

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from exceptions import AuthorizationError, ValidationError
from models import (
    AuthProvider,
    Risk,
    RiskImpact,
    RiskProbability,
    RiskStatus,
    User,
    UserRole,
)
from services.risk_service import RiskService


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
def sample_risk():
    """Create a sample risk for testing."""
    return Risk(
        id=uuid4(),
        project_id=uuid4(),
        title="Test Risk",
        description="This is a test risk",
        probability=RiskProbability.MEDIUM,
        impact=RiskImpact.HIGH,
        status=RiskStatus.OPEN,
    )


@pytest.fixture
def resolved_risk():
    """Create a resolved risk for testing."""
    risk = Risk(
        id=uuid4(),
        project_id=uuid4(),
        title="Resolved Risk",
        description="This risk has been resolved",
        probability=RiskProbability.LOW,
        impact=RiskImpact.LOW,
        status=RiskStatus.CLOSED,
        decision_record="Risk was accepted due to low probability",
        resolved_at=datetime.now(timezone.utc),
        resolved_by_id=uuid4(),
    )
    return risk


class TestResolveRisk:
    """Tests for RiskService.resolve_risk method."""

    def test_only_cogniter_can_resolve(self, mock_session, client_user, sample_risk):
        """Client users should not be able to resolve risks."""
        service = RiskService(mock_session)

        # Mock the repository methods
        with patch.object(service.repository, "get_by_id", return_value=sample_risk):
            with patch.object(
                service.project_repository, "user_has_access", return_value=True
            ):
                with pytest.raises(AuthorizationError) as exc_info:
                    service.resolve_risk(
                        risk_id=sample_risk.id,
                        status=RiskStatus.CLOSED,
                        decision_record="Test resolution",
                        user=client_user,
                    )

                assert "Only Cogniters can resolve risks" in str(exc_info.value)

    def test_cogniter_can_resolve(self, mock_session, cogniter_user, sample_risk):
        """Cogniter users should be able to resolve risks."""
        service = RiskService(mock_session)

        with patch.object(service.repository, "get_by_id", return_value=sample_risk):
            with patch.object(
                service.project_repository, "user_has_access", return_value=True
            ):
                with patch.object(
                    service.repository, "update", return_value=sample_risk
                ):
                    result = service.resolve_risk(
                        risk_id=sample_risk.id,
                        status=RiskStatus.CLOSED,
                        decision_record="Test resolution",
                        user=cogniter_user,
                    )

                    assert result.status == RiskStatus.CLOSED
                    assert result.decision_record == "Test resolution"
                    assert result.resolved_by_id == cogniter_user.id
                    assert result.resolved_at is not None

    def test_requires_decision_record(self, mock_session, cogniter_user, sample_risk):
        """Resolution requires a non-empty decision record."""
        service = RiskService(mock_session)

        with patch.object(service.repository, "get_by_id", return_value=sample_risk):
            with patch.object(
                service.project_repository, "user_has_access", return_value=True
            ):
                with pytest.raises(ValidationError) as exc_info:
                    service.resolve_risk(
                        risk_id=sample_risk.id,
                        status=RiskStatus.CLOSED,
                        decision_record="",
                        user=cogniter_user,
                    )

                assert "Decision record is required" in str(exc_info.value)

    def test_rejects_empty_decision_record(
        self, mock_session, cogniter_user, sample_risk
    ):
        """Resolution rejects whitespace-only decision records."""
        service = RiskService(mock_session)

        with patch.object(service.repository, "get_by_id", return_value=sample_risk):
            with patch.object(
                service.project_repository, "user_has_access", return_value=True
            ):
                with pytest.raises(ValidationError):
                    service.resolve_risk(
                        risk_id=sample_risk.id,
                        status=RiskStatus.CLOSED,
                        decision_record="   ",
                        user=cogniter_user,
                    )

    def test_rejects_open_status(self, mock_session, cogniter_user, sample_risk):
        """Cannot resolve to OPEN status."""
        service = RiskService(mock_session)

        with patch.object(service.repository, "get_by_id", return_value=sample_risk):
            with patch.object(
                service.project_repository, "user_has_access", return_value=True
            ):
                with pytest.raises(ValidationError) as exc_info:
                    service.resolve_risk(
                        risk_id=sample_risk.id,
                        status=RiskStatus.OPEN,
                        decision_record="Test",
                        user=cogniter_user,
                    )

                assert "CLOSED or MITIGATED" in str(exc_info.value)

    def test_sets_resolved_at_and_resolved_by(
        self, mock_session, cogniter_user, sample_risk
    ):
        """Resolution should set timestamp and user automatically."""
        service = RiskService(mock_session)

        with patch.object(service.repository, "get_by_id", return_value=sample_risk):
            with patch.object(
                service.project_repository, "user_has_access", return_value=True
            ):
                with patch.object(
                    service.repository, "update", return_value=sample_risk
                ):
                    service.resolve_risk(
                        risk_id=sample_risk.id,
                        status=RiskStatus.MITIGATED,
                        decision_record="Mitigation complete",
                        user=cogniter_user,
                    )

                    assert sample_risk.resolved_at is not None
                    assert sample_risk.resolved_by_id == cogniter_user.id

    def test_clears_previous_reopen_fields(
        self, mock_session, cogniter_user, sample_risk
    ):
        """Resolution should clear any previous reopen reason."""
        service = RiskService(mock_session)

        # Set some reopen fields
        sample_risk.reopen_reason = "Previous reopen"
        sample_risk.reopened_at = datetime.now(timezone.utc)
        sample_risk.reopened_by_id = uuid4()

        with patch.object(service.repository, "get_by_id", return_value=sample_risk):
            with patch.object(
                service.project_repository, "user_has_access", return_value=True
            ):
                with patch.object(
                    service.repository, "update", return_value=sample_risk
                ):
                    service.resolve_risk(
                        risk_id=sample_risk.id,
                        status=RiskStatus.CLOSED,
                        decision_record="Fresh resolution",
                        user=cogniter_user,
                    )

                    assert sample_risk.reopen_reason is None
                    assert sample_risk.reopened_at is None
                    assert sample_risk.reopened_by_id is None


class TestReopenRisk:
    """Tests for RiskService.reopen_risk method."""

    def test_only_cogniter_can_reopen(self, mock_session, client_user, resolved_risk):
        """Client users should not be able to reopen risks."""
        service = RiskService(mock_session)

        with patch.object(service.repository, "get_by_id", return_value=resolved_risk):
            with patch.object(
                service.project_repository, "user_has_access", return_value=True
            ):
                with pytest.raises(AuthorizationError) as exc_info:
                    service.reopen_risk(
                        risk_id=resolved_risk.id,
                        reason="Need to reopen",
                        user=client_user,
                    )

                assert "Only Cogniters can reopen risks" in str(exc_info.value)

    def test_requires_reason(self, mock_session, cogniter_user, resolved_risk):
        """Reopening requires a non-empty reason."""
        service = RiskService(mock_session)

        with patch.object(service.repository, "get_by_id", return_value=resolved_risk):
            with patch.object(
                service.project_repository, "user_has_access", return_value=True
            ):
                with pytest.raises(ValidationError) as exc_info:
                    service.reopen_risk(
                        risk_id=resolved_risk.id, reason="", user=cogniter_user
                    )

                assert "Reason is required" in str(exc_info.value)

    def test_sets_reopened_at_and_reopened_by(
        self, mock_session, cogniter_user, resolved_risk
    ):
        """Reopening should set timestamp and user automatically."""
        service = RiskService(mock_session)

        with patch.object(service.repository, "get_by_id", return_value=resolved_risk):
            with patch.object(
                service.project_repository, "user_has_access", return_value=True
            ):
                with patch.object(
                    service.repository, "update", return_value=resolved_risk
                ):
                    service.reopen_risk(
                        risk_id=resolved_risk.id,
                        reason="New information received",
                        user=cogniter_user,
                    )

                    assert resolved_risk.reopened_at is not None
                    assert resolved_risk.reopened_by_id == cogniter_user.id

    def test_changes_status_to_open(self, mock_session, cogniter_user, resolved_risk):
        """Reopening should change status back to OPEN."""
        service = RiskService(mock_session)

        with patch.object(service.repository, "get_by_id", return_value=resolved_risk):
            with patch.object(
                service.project_repository, "user_has_access", return_value=True
            ):
                with patch.object(
                    service.repository, "update", return_value=resolved_risk
                ):
                    service.reopen_risk(
                        risk_id=resolved_risk.id,
                        reason="Need to reassess",
                        user=cogniter_user,
                    )

                    assert resolved_risk.status == RiskStatus.OPEN

    def test_cannot_reopen_already_open_risk(
        self, mock_session, cogniter_user, sample_risk
    ):
        """Cannot reopen a risk that is already open."""
        service = RiskService(mock_session)

        with patch.object(service.repository, "get_by_id", return_value=sample_risk):
            with patch.object(
                service.project_repository, "user_has_access", return_value=True
            ):
                with pytest.raises(ValidationError) as exc_info:
                    service.reopen_risk(
                        risk_id=sample_risk.id, reason="Test", user=cogniter_user
                    )

                assert "already open" in str(exc_info.value)


class TestRiskComments:
    """Tests for RiskService comment functionality."""

    def test_client_can_comment_on_assigned_project(
        self, mock_session, client_user, sample_risk
    ):
        """Clients can comment on risks for projects they're assigned to."""
        service = RiskService(mock_session)

        with patch.object(service.repository, "get_by_id", return_value=sample_risk):
            with patch.object(
                service.project_repository, "user_has_access", return_value=True
            ):
                # Should not raise - client has access
                mock_session.add = MagicMock()
                mock_session.commit = MagicMock()
                mock_session.refresh = MagicMock()

                _ = service.add_comment(sample_risk.id, "Test comment", client_user)
                # If we get here without exception, test passes

    def test_client_cannot_comment_on_unassigned_project(
        self, mock_session, client_user, sample_risk
    ):
        """Clients cannot comment on risks for unassigned projects."""
        service = RiskService(mock_session)

        with patch.object(service.repository, "get_by_id", return_value=sample_risk):
            with patch.object(
                service.project_repository, "user_has_access", return_value=False
            ):
                with pytest.raises(AuthorizationError):
                    service.add_comment(sample_risk.id, "Test comment", client_user)

    def test_cogniter_can_comment_on_any_project(
        self, mock_session, cogniter_user, sample_risk
    ):
        """Cogniters can comment on any risk."""
        service = RiskService(mock_session)

        with patch.object(service.repository, "get_by_id", return_value=sample_risk):
            # Cogniters bypass project access check
            mock_session.add = MagicMock()
            mock_session.commit = MagicMock()
            mock_session.refresh = MagicMock()

            _ = service.add_comment(sample_risk.id, "PM comment", cogniter_user)
            # If we get here without exception, test passes

    def test_empty_comment_rejected(self, mock_session, cogniter_user, sample_risk):
        """Empty comments should be rejected."""
        service = RiskService(mock_session)

        with patch.object(service.repository, "get_by_id", return_value=sample_risk):
            with pytest.raises(ValidationError) as exc_info:
                service.add_comment(sample_risk.id, "", cogniter_user)

            assert "content is required" in str(exc_info.value)
