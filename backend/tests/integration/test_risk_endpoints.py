"""Integration tests for Risk endpoints."""

from uuid import uuid4

import pytest

from models import Risk, RiskImpact, RiskProbability, RiskStatus
from models.links import UserProjectLink

# =============================================================================
# Risk Fixtures
# =============================================================================


@pytest.fixture
def sample_risk(session, sample_project) -> Risk:
    """Create a sample risk for testing."""
    risk = Risk(
        id=uuid4(),
        project_id=sample_project.id,
        title="Test Risk",
        description="A test risk that needs attention",
        probability=RiskProbability.MEDIUM,
        impact=RiskImpact.HIGH,
        status=RiskStatus.OPEN,
        mitigation_plan="Monitor and assess weekly",
    )
    session.add(risk)
    session.commit()
    session.refresh(risk)
    return risk


@pytest.fixture
def resolved_risk(session, sample_project, cogniter_user) -> Risk:
    """Create a resolved risk for testing."""
    from datetime import datetime, timezone

    risk = Risk(
        id=uuid4(),
        project_id=sample_project.id,
        title="Resolved Risk",
        description="This risk has been resolved",
        probability=RiskProbability.LOW,
        impact=RiskImpact.LOW,
        status=RiskStatus.CLOSED,
        mitigation_plan="Accepted the risk",
        decision_record="Low probability and impact, accepted",
        resolved_at=datetime.now(timezone.utc),
        resolved_by_id=cogniter_user.id,
    )
    session.add(risk)
    session.commit()
    session.refresh(risk)
    return risk


@pytest.fixture
def project_with_client_and_risk(session, sample_project, client_user, sample_risk):
    """Project with client assigned and a risk."""
    link = UserProjectLink(project_id=sample_project.id, user_id=client_user.id)
    session.add(link)
    session.commit()
    return sample_project


# =============================================================================
# Risk Resolution Tests
# =============================================================================


class TestRiskResolution:
    """Tests for POST /risks/{id}/resolve endpoint."""

    def test_resolve_endpoint_cogniter_success(self, authenticated_client, sample_risk):
        """Cogniter should be able to resolve a risk with decision record."""
        response = authenticated_client.post(
            f"/risks/{sample_risk.id}/resolve",
            json={
                "status": "Closed",
                "decision_record": "Risk mitigated by implementing controls",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "Closed"
        assert data["decision_record"] == "Risk mitigated by implementing controls"
        assert data["resolved_at"] is not None
        assert data["resolved_by_id"] is not None

    def test_resolve_endpoint_client_forbidden(
        self,
        client,
        client_user,
        sample_risk,
        create_token,
        project_with_client_and_risk,
    ):
        """Client should NOT be able to resolve risks - 403 forbidden."""
        token = create_token(client_user)
        client.headers["Authorization"] = f"Bearer {token}"

        response = client.post(
            f"/risks/{sample_risk.id}/resolve",
            json={"status": "Closed", "decision_record": "Trying to close"},
        )

        assert response.status_code == 403

    def test_resolve_requires_decision_record(self, authenticated_client, sample_risk):
        """Resolution without decision record should fail."""
        response = authenticated_client.post(
            f"/risks/{sample_risk.id}/resolve",
            json={"status": "Mitigated", "decision_record": ""},
        )

        # Should fail validation
        assert response.status_code == 422

    def test_resolve_with_mitigated_status(self, authenticated_client, sample_risk):
        """Should be able to resolve with MITIGATED status."""
        response = authenticated_client.post(
            f"/risks/{sample_risk.id}/resolve",
            json={
                "status": "Mitigated",
                "decision_record": "Mitigation plan fully implemented",
            },
        )

        assert response.status_code == 200
        assert response.json()["status"] == "Mitigated"


class TestRiskReopen:
    """Tests for POST /risks/{id}/reopen endpoint."""

    def test_reopen_endpoint_requires_reason(self, authenticated_client, resolved_risk):
        """Reopening without reason should fail."""
        response = authenticated_client.post(
            f"/risks/{resolved_risk.id}/reopen", json={"reason": ""}
        )

        assert response.status_code == 422

    def test_reopen_endpoint_cogniter_success(
        self, authenticated_client, resolved_risk
    ):
        """Cogniter should be able to reopen a resolved risk."""
        response = authenticated_client.post(
            f"/risks/{resolved_risk.id}/reopen",
            json={"reason": "New information suggests risk is still present"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "Open"
        assert data["reopen_reason"] == "New information suggests risk is still present"
        assert data["reopened_at"] is not None

    def test_reopen_endpoint_client_forbidden(
        self, client, client_user, resolved_risk, create_token, session, sample_project
    ):
        """Client should NOT be able to reopen risks."""
        # Assign client to the project first
        link = UserProjectLink(project_id=sample_project.id, user_id=client_user.id)
        session.add(link)
        session.commit()

        token = create_token(client_user)
        client.headers["Authorization"] = f"Bearer {token}"

        response = client.post(
            f"/risks/{resolved_risk.id}/reopen", json={"reason": "Trying to reopen"}
        )

        assert response.status_code == 403


class TestRiskComments:
    """Tests for risk comment endpoints."""

    def test_client_can_add_comment(
        self,
        client,
        client_user,
        sample_risk,
        create_token,
        project_with_client_and_risk,
    ):
        """Assigned client should be able to add comments to risks."""
        token = create_token(client_user)
        client.headers["Authorization"] = f"Bearer {token}"

        response = client.post(
            f"/risks/{sample_risk.id}/comments",
            json={"content": "This is a client comment"},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["content"] == "This is a client comment"
        assert data["user_id"] == str(client_user.id)

    def test_comment_requires_project_assignment(
        self, client, client_user, sample_risk, create_token
    ):
        """Unassigned client should NOT be able to comment."""
        token = create_token(client_user)
        client.headers["Authorization"] = f"Bearer {token}"

        response = client.post(
            f"/risks/{sample_risk.id}/comments",
            json={"content": "Trying to comment without access"},
        )

        assert response.status_code == 403

    def test_cogniter_can_comment_on_any_risk(self, authenticated_client, sample_risk):
        """Cogniters should be able to comment on any risk."""
        response = authenticated_client.post(
            f"/risks/{sample_risk.id}/comments",
            json={"content": "PM comment for tracking"},
        )

        assert response.status_code == 201
        assert response.json()["content"] == "PM comment for tracking"

    def test_get_comments(self, authenticated_client, sample_risk):
        """Should be able to retrieve comments for a risk."""
        # First add a comment
        authenticated_client.post(
            f"/risks/{sample_risk.id}/comments", json={"content": "First comment"}
        )

        # Then retrieve
        response = authenticated_client.get(f"/risks/{sample_risk.id}/comments")

        assert response.status_code == 200
        comments = response.json()
        assert len(comments) >= 1
        assert any(c["content"] == "First comment" for c in comments)


class TestRiskAccessControl:
    """Tests for risk access control."""

    def test_unassigned_client_cannot_view_risks(
        self, client, client_user, sample_project, create_token
    ):
        """Unassigned client should get 403 when viewing risks."""
        token = create_token(client_user)
        client.headers["Authorization"] = f"Bearer {token}"

        response = client.get(f"/risks/?project_id={sample_project.id}")

        assert response.status_code == 403

    def test_assigned_client_can_view_risks(
        self,
        client,
        client_user,
        sample_risk,
        create_token,
        project_with_client_and_risk,
    ):
        """Assigned client should be able to view project risks."""
        token = create_token(client_user)
        client.headers["Authorization"] = f"Bearer {token}"

        response = client.get(f"/risks/?project_id={sample_risk.project_id}")

        assert response.status_code == 200
        risks = response.json()
        assert len(risks) >= 1

    def test_cogniter_can_view_all_risks(self, authenticated_client, sample_risk):
        """Cogniters should be able to view any project's risks."""
        response = authenticated_client.get(
            f"/risks/?project_id={sample_risk.project_id}"
        )

        assert response.status_code == 200
