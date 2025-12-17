"""Integration tests for project API endpoints."""
import pytest
from uuid import uuid4


class TestListProjects:
    """Tests for GET /projects endpoint."""
    
    def test_unauthenticated_request_returns_401(self, client):
        """Requests without auth should return 401."""
        response = client.get("/projects/")
        
        assert response.status_code == 401
    
    def test_authenticated_request_returns_projects(
        self, 
        authenticated_client, 
        sample_project
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
    
    def test_client_gets_403_on_create(
        self, 
        client, 
        client_user, 
        create_token
    ):
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

