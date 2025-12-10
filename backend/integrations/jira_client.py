"""Jira API client for fetching project data."""
import httpx
from typing import Optional
from dataclasses import dataclass
from datetime import datetime, timedelta

from config import Settings
from exceptions import IntegrationError


@dataclass
class JiraProject:
    """Jira project data."""
    key: str
    name: str
    id: str
    project_type: str


@dataclass
class JiraIssue:
    """Jira issue data."""
    key: str
    summary: str
    status: str
    issue_type: str
    assignee: Optional[str]
    priority: Optional[str]
    created: str
    updated: str


@dataclass
class JiraSprint:
    """Jira sprint data."""
    id: int
    name: str
    state: str  # active, closed, future
    start_date: Optional[str]
    end_date: Optional[str]
    goal: Optional[str]


class JiraClient:
    """Client for interacting with Jira Cloud API using OAuth 2.0."""
    
    # Atlassian OAuth endpoints
    AUTH_URL = "https://auth.atlassian.com/oauth/token"
    RESOURCES_URL = "https://api.atlassian.com/oauth/token/accessible-resources"
    
    def __init__(self, settings: Settings):
        self.base_url = settings.jira_base_url.rstrip("/")
        self.client_id = settings.jira_client_id
        self.client_secret = settings.jira_client_secret
        self.cloud_id = settings.jira_cloud_id
        self._client: Optional[httpx.AsyncClient] = None
        self._access_token: Optional[str] = None
        self._token_expires_at: Optional[datetime] = None
    
    @property
    def is_configured(self) -> bool:
        """Check if Jira OAuth credentials are configured."""
        return bool(self.client_id and self.client_secret)
    
    async def _get_access_token(self) -> str:
        """Get OAuth access token, refreshing if needed."""
        # Check if we have a valid token
        if self._access_token and self._token_expires_at:
            if datetime.utcnow() < self._token_expires_at - timedelta(minutes=5):
                return self._access_token
        
        # Get new token
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.AUTH_URL,
                data={
                    "grant_type": "client_credentials",
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            
            if response.status_code != 200:
                raise IntegrationError(
                    f"Jira OAuth failed: {response.status_code} - {response.text}"
                )
            
            data = response.json()
            self._access_token = data["access_token"]
            expires_in = data.get("expires_in", 3600)
            self._token_expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
            
            return self._access_token
    
    async def _get_cloud_id(self) -> str:
        """Get the Jira Cloud ID from accessible resources."""
        if self.cloud_id:
            return self.cloud_id
        
        token = await self._get_access_token()
        async with httpx.AsyncClient() as client:
            response = await client.get(
                self.RESOURCES_URL,
                headers={"Authorization": f"Bearer {token}"}
            )
            
            if response.status_code != 200:
                raise IntegrationError(
                    f"Failed to get Jira resources: {response.status_code} - {response.text}"
                )
            
            resources = response.json()
            if not resources:
                raise IntegrationError("No Jira sites accessible with these credentials.")
            
            # Use the first accessible site, or match by base_url if provided
            for resource in resources:
                if self.base_url and self.base_url in resource.get("url", ""):
                    self.cloud_id = resource["id"]
                    return self.cloud_id
            
            # Default to first resource
            self.cloud_id = resources[0]["id"]
            return self.cloud_id
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client with OAuth token."""
        token = await self._get_access_token()
        cloud_id = await self._get_cloud_id()
        
        # Jira Cloud API base URL with cloud ID
        api_base = f"https://api.atlassian.com/ex/jira/{cloud_id}"
        
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=api_base,
                timeout=30.0,
                headers={
                    "Accept": "application/json",
                    "Authorization": f"Bearer {token}"
                }
            )
        else:
            # Update token in existing client
            self._client.headers["Authorization"] = f"Bearer {token}"
        
        return self._client
    
    async def close(self):
        """Close the HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
    
    async def test_connection(self) -> dict:
        """
        Test the Jira connection and return server info.
        Raises IntegrationError if connection fails.
        """
        if not self.is_configured:
            raise IntegrationError(
                "Jira is not configured. Set JIRA_CLIENT_ID and JIRA_CLIENT_SECRET."
            )
        
        try:
            client = await self._get_client()
            response = await client.get("/rest/api/3/myself")
            
            if response.status_code == 401:
                raise IntegrationError(
                    "Jira authentication failed. Check your email and API token."
                )
            elif response.status_code == 403:
                raise IntegrationError(
                    "Jira access forbidden. Check your permissions."
                )
            elif response.status_code != 200:
                raise IntegrationError(
                    f"Jira connection failed with status {response.status_code}: {response.text}"
                )
            
            user_data = response.json()
            return {
                "status": "connected",
                "user": user_data.get("displayName", "Unknown"),
                "email": user_data.get("emailAddress", "Unknown"),
                "account_id": user_data.get("accountId", "Unknown"),
            }
        except httpx.ConnectError as e:
            raise IntegrationError(f"Cannot connect to Jira at {self.base_url}: {str(e)}")
        except httpx.TimeoutException:
            raise IntegrationError(f"Jira connection timed out: {self.base_url}")
    
    async def get_project(self, project_key: str) -> JiraProject:
        """Fetch a Jira project by key."""
        if not self.is_configured:
            raise IntegrationError("Jira is not configured.")
        
        try:
            client = await self._get_client()
            response = await client.get(f"/rest/api/3/project/{project_key}")
            
            if response.status_code == 404:
                raise IntegrationError(f"Jira project '{project_key}' not found.")
            elif response.status_code != 200:
                raise IntegrationError(
                    f"Failed to fetch Jira project: {response.status_code} - {response.text}"
                )
            
            data = response.json()
            return JiraProject(
                key=data["key"],
                name=data["name"],
                id=data["id"],
                project_type=data.get("projectTypeKey", "unknown"),
            )
        except httpx.HTTPError as e:
            raise IntegrationError(f"Jira API error: {str(e)}")
    
    async def get_project_issues(
        self, 
        project_key: str, 
        max_results: int = 100
    ) -> list[JiraIssue]:
        """Fetch issues for a Jira project."""
        if not self.is_configured:
            raise IntegrationError("Jira is not configured.")
        
        try:
            client = await self._get_client()
            jql = f"project = {project_key} ORDER BY created DESC"
            
            response = await client.get(
                "/rest/api/3/search",
                params={
                    "jql": jql,
                    "maxResults": max_results,
                    "fields": "summary,status,issuetype,assignee,priority,created,updated"
                }
            )
            
            if response.status_code != 200:
                raise IntegrationError(
                    f"Failed to fetch Jira issues: {response.status_code} - {response.text}"
                )
            
            data = response.json()
            issues = []
            
            for issue in data.get("issues", []):
                fields = issue.get("fields", {})
                assignee = fields.get("assignee")
                priority = fields.get("priority")
                
                issues.append(JiraIssue(
                    key=issue["key"],
                    summary=fields.get("summary", ""),
                    status=fields.get("status", {}).get("name", "Unknown"),
                    issue_type=fields.get("issuetype", {}).get("name", "Unknown"),
                    assignee=assignee.get("displayName") if assignee else None,
                    priority=priority.get("name") if priority else None,
                    created=fields.get("created", ""),
                    updated=fields.get("updated", ""),
                ))
            
            return issues
        except httpx.HTTPError as e:
            raise IntegrationError(f"Jira API error: {str(e)}")
    
    async def get_board_sprints(
        self, 
        board_id: int, 
        state: Optional[str] = None
    ) -> list[JiraSprint]:
        """
        Fetch sprints for a Jira board.
        
        Args:
            board_id: The Jira board ID
            state: Filter by sprint state ('active', 'closed', 'future')
        """
        if not self.is_configured:
            raise IntegrationError("Jira is not configured.")
        
        try:
            client = await self._get_client()
            params = {"maxResults": 50}
            if state:
                params["state"] = state
            
            response = await client.get(
                f"/rest/agile/1.0/board/{board_id}/sprint",
                params=params
            )
            
            if response.status_code == 404:
                raise IntegrationError(f"Jira board {board_id} not found.")
            elif response.status_code != 200:
                raise IntegrationError(
                    f"Failed to fetch sprints: {response.status_code} - {response.text}"
                )
            
            data = response.json()
            sprints = []
            
            for sprint in data.get("values", []):
                sprints.append(JiraSprint(
                    id=sprint["id"],
                    name=sprint["name"],
                    state=sprint.get("state", "unknown"),
                    start_date=sprint.get("startDate"),
                    end_date=sprint.get("endDate"),
                    goal=sprint.get("goal"),
                ))
            
            return sprints
        except httpx.HTTPError as e:
            raise IntegrationError(f"Jira API error: {str(e)}")
    
    async def get_sprint_issues(
        self, 
        sprint_id: int, 
        max_results: int = 100
    ) -> list[JiraIssue]:
        """Fetch issues for a specific sprint."""
        if not self.is_configured:
            raise IntegrationError("Jira is not configured.")
        
        try:
            client = await self._get_client()
            jql = f"sprint = {sprint_id} ORDER BY rank ASC"
            
            response = await client.get(
                "/rest/api/3/search",
                params={
                    "jql": jql,
                    "maxResults": max_results,
                    "fields": "summary,status,issuetype,assignee,priority,created,updated"
                }
            )
            
            if response.status_code != 200:
                raise IntegrationError(
                    f"Failed to fetch sprint issues: {response.status_code} - {response.text}"
                )
            
            data = response.json()
            issues = []
            
            for issue in data.get("issues", []):
                fields = issue.get("fields", {})
                assignee = fields.get("assignee")
                priority = fields.get("priority")
                
                issues.append(JiraIssue(
                    key=issue["key"],
                    summary=fields.get("summary", ""),
                    status=fields.get("status", {}).get("name", "Unknown"),
                    issue_type=fields.get("issuetype", {}).get("name", "Unknown"),
                    assignee=assignee.get("displayName") if assignee else None,
                    priority=priority.get("name") if priority else None,
                    created=fields.get("created", ""),
                    updated=fields.get("updated", ""),
                ))
            
            return issues
        except httpx.HTTPError as e:
            raise IntegrationError(f"Jira API error: {str(e)}")

