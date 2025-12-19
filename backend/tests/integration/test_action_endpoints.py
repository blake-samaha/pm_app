"""Integration tests for Action endpoints."""

from uuid import uuid4

import pytest

from models import ActionItem, ActionStatus, Priority
from models.links import UserProjectLink

# =============================================================================
# Action Fixtures
# =============================================================================


@pytest.fixture
def sample_action(session, sample_project) -> ActionItem:
    """Create a sample action item for testing."""
    action = ActionItem(
        id=uuid4(),
        project_id=sample_project.id,
        title="Test Action Item",
        status=ActionStatus.TO_DO,
        priority=Priority.MEDIUM,
        assignee="Test User",
    )
    session.add(action)
    session.commit()
    session.refresh(action)
    return action


@pytest.fixture
def project_with_client_and_action(session, sample_project, client_user, sample_action):
    """Project with client assigned and an action item."""
    sample_project.is_published = True
    session.add(sample_project)
    link = UserProjectLink(project_id=sample_project.id, user_id=client_user.id)
    session.add(link)
    session.commit()
    return sample_project


# =============================================================================
# Action Comment Tests
# =============================================================================


class TestActionComments:
    """Tests for action comment endpoints."""

    def test_cogniter_can_add_comment(self, authenticated_client, sample_action):
        """Cogniters should be able to add comments to any action."""
        response = authenticated_client.post(
            f"/actions/{sample_action.id}/comments",
            json={"content": "PM comment for tracking"},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["content"] == "PM comment for tracking"
        assert data["author_name"] is not None
        assert data["author_email"] is not None

    def test_client_can_add_comment(
        self, client, client_user, sample_action, create_token, session, sample_project
    ):
        """Assigned client should be able to add comments to actions."""
        # First assign client to the project
        sample_project.is_published = True
        session.add(sample_project)
        link = UserProjectLink(project_id=sample_project.id, user_id=client_user.id)
        session.add(link)
        session.commit()

        # Auth as client
        token = create_token(client_user)
        client.headers["Authorization"] = f"Bearer {token}"

        response = client.post(
            f"/actions/{sample_action.id}/comments",
            json={"content": "This is a client comment"},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["content"] == "This is a client comment"
        assert data["author_name"] == client_user.name
        assert data["author_email"] == client_user.email

    def test_comment_requires_project_assignment(
        self, client, client_user, sample_action, create_token
    ):
        """Unassigned client should NOT be able to comment."""
        # Auth as client without assignment
        token = create_token(client_user)
        client.headers["Authorization"] = f"Bearer {token}"

        response = client.post(
            f"/actions/{sample_action.id}/comments",
            json={"content": "Trying to comment without access"},
        )

        assert response.status_code == 403

    def test_empty_comment_rejected(self, authenticated_client, sample_action):
        """Empty comments should be rejected with 422."""
        response = authenticated_client.post(
            f"/actions/{sample_action.id}/comments",
            json={"content": ""},
        )

        assert response.status_code == 422

    def test_whitespace_only_comment_rejected(
        self, authenticated_client, sample_action
    ):
        """Whitespace-only comments should be rejected."""
        response = authenticated_client.post(
            f"/actions/{sample_action.id}/comments",
            json={"content": "   "},
        )

        assert response.status_code == 422

    def test_get_comments(self, authenticated_client, sample_action):
        """Should be able to retrieve comments for an action."""
        # First add a comment
        authenticated_client.post(
            f"/actions/{sample_action.id}/comments", json={"content": "First comment"}
        )

        # Get comments
        response = authenticated_client.get(f"/actions/{sample_action.id}/comments")

        assert response.status_code == 200
        comments = response.json()
        assert len(comments) >= 1
        assert any(c["content"] == "First comment" for c in comments)

    def test_comments_ordered_by_created_at(self, authenticated_client, sample_action):
        """Comments should be returned in chronological order (oldest first)."""
        # Add multiple comments
        authenticated_client.post(
            f"/actions/{sample_action.id}/comments", json={"content": "First"}
        )
        authenticated_client.post(
            f"/actions/{sample_action.id}/comments", json={"content": "Second"}
        )
        authenticated_client.post(
            f"/actions/{sample_action.id}/comments", json={"content": "Third"}
        )

        # Get comments
        response = authenticated_client.get(f"/actions/{sample_action.id}/comments")

        assert response.status_code == 200
        comments = response.json()
        assert len(comments) >= 3

        # Verify order
        contents = [c["content"] for c in comments]
        first_idx = contents.index("First")
        second_idx = contents.index("Second")
        third_idx = contents.index("Third")
        assert first_idx < second_idx < third_idx

    def test_comments_include_author_fields(self, authenticated_client, sample_action):
        """Comments should include author_name and author_email."""
        # Add a comment
        authenticated_client.post(
            f"/actions/{sample_action.id}/comments", json={"content": "Test comment"}
        )

        # Get comments
        response = authenticated_client.get(f"/actions/{sample_action.id}/comments")

        assert response.status_code == 200
        comments = response.json()
        assert len(comments) >= 1

        comment = comments[-1]
        assert "author_name" in comment
        assert "author_email" in comment
        assert comment["author_name"] is not None
        assert comment["author_email"] is not None


# =============================================================================
# Action List with Comment Count Tests
# =============================================================================


class TestActionListCommentCount:
    """Tests for action list with comment counts."""

    def test_actions_include_comment_count(self, authenticated_client, sample_action):
        """Action list should include comment_count for each action."""
        response = authenticated_client.get(
            f"/actions/?project_id={sample_action.project_id}"
        )

        assert response.status_code == 200
        actions = response.json()
        assert len(actions) >= 1

        action = next(a for a in actions if a["id"] == str(sample_action.id))
        assert "comment_count" in action
        assert action["comment_count"] == 0

    def test_comment_count_increments(self, authenticated_client, sample_action):
        """Comment count should increment when comments are added."""
        # Check initial count
        response = authenticated_client.get(
            f"/actions/?project_id={sample_action.project_id}"
        )
        actions = response.json()
        action = next(a for a in actions if a["id"] == str(sample_action.id))
        assert action["comment_count"] == 0

        # Add a comment
        authenticated_client.post(
            f"/actions/{sample_action.id}/comments", json={"content": "New comment"}
        )

        # Check count again
        response = authenticated_client.get(
            f"/actions/?project_id={sample_action.project_id}"
        )
        actions = response.json()
        action = next(a for a in actions if a["id"] == str(sample_action.id))
        assert action["comment_count"] == 1

        # Add another comment
        authenticated_client.post(
            f"/actions/{sample_action.id}/comments", json={"content": "Another comment"}
        )

        # Check count again
        response = authenticated_client.get(
            f"/actions/?project_id={sample_action.project_id}"
        )
        actions = response.json()
        action = next(a for a in actions if a["id"] == str(sample_action.id))
        assert action["comment_count"] == 2
