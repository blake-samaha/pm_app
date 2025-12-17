"""Jira API client for fetching project data."""
import base64
import httpx
from typing import Optional
from dataclasses import dataclass

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
    due_date: Optional[str] = None


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
    """Client for interacting with Jira Cloud API using API Token authentication."""
    
    def __init__(self, settings: Settings):
        self.base_url = settings.jira_base_url.rstrip("/")
        self.email = settings.jira_email
        self.api_token = settings.jira_api_token
        self._client: Optional[httpx.AsyncClient] = None
    
    @property
    def is_configured(self) -> bool:
        """Check if Jira API token credentials are configured."""
        return bool(self.base_url and self.email and self.api_token)
    
    def _get_auth_header(self) -> str:
        """Generate Basic auth header from email and API token."""
        credentials = f"{self.email}:{self.api_token}"
        encoded = base64.b64encode(credentials.encode()).decode()
        return f"Basic {encoded}"

    async def _search_issues(
        self,
        jql: str,
        max_results: int,
        fields: list[str],
    ) -> list[dict]:
        """
        Execute the Jira search/jql API and return raw issue payloads.

        Handles Atlassian's batched response shape (responses[0].issues) and
        paginates until max_results is reached or no more issues are returned.
        """
        if max_results <= 0:
            return []

        issues: list[dict] = []
        start_at = 0
        page_size = min(max_results, 100)  # Jira typically caps at 100 per page

        client = await self._get_client()

        while len(issues) < max_results:
            response = await client.get(
                "/rest/api/3/search/jql",
                params={
                    "jql": jql,
                    "startAt": start_at,
                    "maxResults": page_size,
                    "fields": ",".join(fields) if fields else None,
                },
            )

            if response.status_code == 410:
                raise IntegrationError(
                    "Jira API search endpoint deprecated; ensure /rest/api/3/search/jql is used."
                )
            if response.status_code != 200:
                raise IntegrationError(
                    f"Failed to fetch Jira issues: {response.status_code} - {response.text}"
                )

            data = response.json()
            responses = data.get("responses") or []
            first = responses[0] if responses else {}
            issue_list = first.get("issues") if first else data.get("issues", [])

            current_batch = issue_list or []
            issues.extend(current_batch)

            received = len(current_batch)
            if received < page_size:
                break
            start_at += received

        return issues[:max_results]
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client with API token authentication."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=30.0,
                headers={
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                    "Authorization": self._get_auth_header()
                }
            )
        
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
                "Jira is not configured. Set JIRA_BASE_URL, JIRA_EMAIL, and JIRA_API_TOKEN."
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
            raise IntegrationError(f"Cannot connect to Jira at {self.base_url}: {str(e)}") from e
        except httpx.TimeoutException as e:
            raise IntegrationError(f"Jira connection timed out: {self.base_url}") from e
    
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
            raise IntegrationError(f"Jira API error: {str(e)}") from e
    
    async def get_project_issues(
        self, 
        project_key: str, 
        max_results: int = 100
    ) -> list[JiraIssue]:
        """Fetch issues for a Jira project using the current JQL search API."""
        if not self.is_configured:
            raise IntegrationError("Jira is not configured.")
        
        try:
            jql = f"project = {project_key} ORDER BY created DESC"
            raw_issues = await self._search_issues(
                jql=jql,
                max_results=max_results,
                fields=[
                    "summary",
                    "status",
                    "issuetype",
                    "assignee",
                    "priority",
                    "created",
                    "updated",
                    "duedate",
                ],
            )

            issues: list[JiraIssue] = []
            for issue in raw_issues:
                fields = issue.get("fields", {})
                assignee = fields.get("assignee")
                priority = fields.get("priority")

                issues.append(
                    JiraIssue(
                        key=issue["key"],
                        summary=fields.get("summary", ""),
                        status=fields.get("status", {}).get("name", "Unknown"),
                        issue_type=fields.get("issuetype", {}).get("name", "Unknown"),
                        assignee=assignee.get("displayName") if assignee else None,
                        priority=priority.get("name") if priority else None,
                        created=fields.get("created", ""),
                        updated=fields.get("updated", ""),
                        due_date=fields.get("duedate"),
                    )
                )

            return issues
        except httpx.HTTPError as e:
            raise IntegrationError(f"Jira API error: {str(e)}") from e
    
    async def get_project_boards(self, project_key: str) -> list[dict]:
        """
        Get boards associated with a Jira project.
        Returns list of boards with 'id' and 'name' fields.
        """
        if not self.is_configured:
            raise IntegrationError("Jira is not configured.")
        
        try:
            client = await self._get_client()
            # Use Agile API to get boards for a project
            response = await client.get(
                "/rest/agile/1.0/board",
                params={"projectKeyOrId": project_key, "maxResults": 50}
            )
            
            if response.status_code != 200:
                raise IntegrationError(
                    f"Failed to fetch boards: {response.status_code} - {response.text}"
                )
            
            data = response.json()
            return data.get("values", [])
        except httpx.HTTPError as e:
            raise IntegrationError(f"Jira API error: {str(e)}") from e
    
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
            raise IntegrationError(f"Jira API error: {str(e)}") from e
            
    async def get_active_sprint_goal(self, board_id: int) -> Optional[str]:
        """
        Get the goal of the active sprint for a board.
        Returns None if no active sprint or no goal set.
        """
        try:
            sprints = await self.get_board_sprints(board_id, state="active")
            if sprints and sprints[0].goal:
                return sprints[0].goal
            return None
        except IntegrationError:
            # Swallow errors for sprint goal fetch as it's secondary data
            return None
    
    async def get_sprint_issues(
        self, 
        sprint_id: int, 
        max_results: int = 100
    ) -> list[JiraIssue]:
        """Fetch issues for a specific sprint using the current JQL search API."""
        if not self.is_configured:
            raise IntegrationError("Jira is not configured.")
        
        try:
            jql = f"sprint = {sprint_id} ORDER BY rank ASC"
            raw_issues = await self._search_issues(
                jql=jql,
                max_results=max_results,
                fields=[
                    "summary",
                    "status",
                    "issuetype",
                    "assignee",
                    "priority",
                    "created",
                    "updated",
                    "duedate",
                ],
            )

            issues: list[JiraIssue] = []
            for issue in raw_issues:
                fields = issue.get("fields", {})
                assignee = fields.get("assignee")
                priority = fields.get("priority")

                issues.append(
                    JiraIssue(
                        key=issue["key"],
                        summary=fields.get("summary", ""),
                        status=fields.get("status", {}).get("name", "Unknown"),
                        issue_type=fields.get("issuetype", {}).get("name", "Unknown"),
                        assignee=assignee.get("displayName") if assignee else None,
                        priority=priority.get("name") if priority else None,
                        created=fields.get("created", ""),
                        updated=fields.get("updated", ""),
                        due_date=fields.get("duedate"),
                    )
                )

            return issues
        except httpx.HTTPError as e:
            raise IntegrationError(f"Jira API error: {str(e)}") from e
