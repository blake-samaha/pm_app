"""Integration tests for project API endpoints."""

from uuid import uuid4


class TestListProjects:
    """Tests for GET /projects endpoint."""

    def test_unauthenticated_request_returns_401(self, client):
        """Requests without auth should return 401."""
        response = client.get("/projects/")

        assert response.status_code == 401

    def test_authenticated_request_returns_projects(
        self, authenticated_client, sample_project
    ):
        """Authenticated requests should return project list."""
        response = authenticated_client.get("/projects/")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestCreateProject:
    """Tests for POST /projects endpoint."""

    def test_cogniter_can_create_project(self, authenticated_client):
        """Cogniters should be able to create projects via API."""
        project_data = {
            "name": "API Test Project",
            "type": "Fixed Price",
            "precursive_url": "https://precursive.example.com/api-test",
        }

        response = authenticated_client.post("/projects/", json=project_data)

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "API Test Project"
        assert "id" in data

    def test_client_gets_403_on_create(self, client, client_user, create_token):
        """Clients should get 403 Forbidden when creating projects."""
        token = create_token(client_user)
        client.headers["Authorization"] = f"Bearer {token}"

        project_data = {
            "name": "Unauthorized Project",
            "type": "Fixed Price",
            "precursive_url": "https://precursive.example.com/unauth",
        }

        response = client.post("/projects/", json=project_data)

        assert response.status_code == 403


class TestGetProject:
    """Tests for GET /projects/{id} endpoint."""

    def test_get_existing_project(self, authenticated_client, sample_project):
        """Should return project details for existing project."""
        response = authenticated_client.get(f"/projects/{sample_project.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(sample_project.id)
        assert data["name"] == sample_project.name

    def test_get_nonexistent_project_returns_404(self, authenticated_client):
        """Should return 404 for non-existent project."""
        fake_id = uuid4()

        response = authenticated_client.get(f"/projects/{fake_id}")

        assert response.status_code == 404


class TestClientAccessControl:
    """Tests for Client access control on projects - TDD: P0 Security Fix."""

    def test_unassigned_client_sees_empty_project_list(
        self, client, client_user, sample_project, create_token
    ):
        """Client with no project assignments should see empty list."""
        token = create_token(client_user)
        client.headers["Authorization"] = f"Bearer {token}"

        response = client.get("/projects/")

        assert response.status_code == 200
        assert response.json() == []

    def test_assigned_client_sees_only_published_project(
        self,
        client,
        session,
        client_user,
        sample_project,
        second_project,
        project_with_client_assigned,
        create_token,
    ):
        """Client assigned to one *published* project should see only that project."""
        # Publish the project before listing (clients only see published projects)
        project_with_client_assigned.is_published = True
        session.add(project_with_client_assigned)
        session.commit()

        token = create_token(client_user)
        client.headers["Authorization"] = f"Bearer {token}"

        response = client.get("/projects/")

        assert response.status_code == 200
        projects = response.json()
        assert len(projects) == 1
        assert projects[0]["id"] == str(sample_project.id)

    def test_assigned_client_does_not_see_draft_project(
        self, client, client_user, project_with_client_assigned, create_token
    ):
        """Client assigned to a draft project should see an empty list until it is published."""
        token = create_token(client_user)
        client.headers["Authorization"] = f"Bearer {token}"

        response = client.get("/projects/")

        assert response.status_code == 200
        assert response.json() == []

    def test_client_cannot_access_unassigned_project_details(
        self, client, client_user, sample_project, create_token
    ):
        """Client should get 403 for unassigned project details."""
        token = create_token(client_user)
        client.headers["Authorization"] = f"Bearer {token}"

        response = client.get(f"/projects/{sample_project.id}")

        assert response.status_code == 403

    def test_client_can_access_assigned_project_details(
        self, client, session, client_user, project_with_client_assigned, create_token
    ):
        """Client should be able to access assigned project details only when published."""
        project_with_client_assigned.is_published = True
        session.add(project_with_client_assigned)
        session.commit()

        token = create_token(client_user)
        client.headers["Authorization"] = f"Bearer {token}"

        response = client.get(f"/projects/{project_with_client_assigned.id}")

        assert response.status_code == 200

    def test_client_cannot_get_actions_for_unassigned_project(
        self, client, client_user, sample_project, create_token
    ):
        """Client should get 403 when fetching actions for unassigned project."""
        token = create_token(client_user)
        client.headers["Authorization"] = f"Bearer {token}"

        response = client.get(f"/actions/?project_id={sample_project.id}")

        assert response.status_code == 403

    def test_client_cannot_get_risks_for_unassigned_project(
        self, client, client_user, sample_project, create_token
    ):
        """Client should get 403 when fetching risks for unassigned project."""
        token = create_token(client_user)
        client.headers["Authorization"] = f"Bearer {token}"

        response = client.get(f"/risks/?project_id={sample_project.id}")

        assert response.status_code == 403

    def test_client_financials_also_requires_assignment(
        self, client, client_financials_user, sample_project, create_token
    ):
        """Client + Financials role should also require project assignment."""
        token = create_token(client_financials_user)
        client.headers["Authorization"] = f"Bearer {token}"

        response = client.get("/projects/")

        assert response.status_code == 200
        assert response.json() == []

    def test_cogniter_sees_all_projects(
        self, authenticated_client, sample_project, second_project
    ):
        """Cogniters should see all projects regardless of assignment."""
        response = authenticated_client.get("/projects/")

        assert response.status_code == 200
        projects = response.json()
        # Cogniter should see at least both sample_project and second_project
        assert len(projects) >= 2


class TestFinancialFieldLevelAccess:
    """Tests for server-side enforcement of financial visibility."""

    def test_financials_hidden_for_regular_client(
        self,
        client,
        session,
        client_user,
        client_financials_user,
        sample_project,
        create_token,
    ):
        """Regular Client should not receive financial fields even if project has them."""
        from models.links import UserProjectLink

        # Publish and assign both users
        sample_project.is_published = True
        sample_project.total_budget = 1000
        sample_project.spent_budget = 250
        sample_project.remaining_budget = 750
        session.add(sample_project)
        session.add(
            UserProjectLink(project_id=sample_project.id, user_id=client_user.id)
        )
        session.add(
            UserProjectLink(
                project_id=sample_project.id, user_id=client_financials_user.id
            )
        )
        session.commit()

        # Regular client should see financials stripped
        token = create_token(client_user)
        client.headers["Authorization"] = f"Bearer {token}"
        resp = client.get(f"/projects/{sample_project.id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_budget"] is None
        assert data["spent_budget"] is None
        assert data["remaining_budget"] is None

        # Client + Financials should see values
        token = create_token(client_financials_user)
        client.headers["Authorization"] = f"Bearer {token}"
        resp = client.get(f"/projects/{sample_project.id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_budget"] == 1000
        assert data["spent_budget"] == 250
        assert data["remaining_budget"] == 750
