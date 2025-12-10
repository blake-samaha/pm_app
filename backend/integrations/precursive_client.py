"""Precursive/Salesforce API client for fetching project and financial data."""
import httpx
from typing import Optional
from dataclasses import dataclass
from datetime import datetime

from config import Settings
from exceptions import IntegrationError


@dataclass
class SalesforceToken:
    """Salesforce OAuth token data."""
    access_token: str
    instance_url: str
    token_type: str
    issued_at: datetime


@dataclass
class PrecursiveProject:
    """Precursive project data from Salesforce."""
    id: str
    name: str
    status: str
    delivery_phase: Optional[str]
    project_type: Optional[str]
    start_date: Optional[str]
    end_date: Optional[str]
    client_name: Optional[str]


@dataclass 
class PrecursiveFinancials:
    """Financial data from Precursive/Salesforce."""
    project_id: str
    total_budget: Optional[float]
    spent_budget: Optional[float]
    remaining_budget: Optional[float]
    revenue: Optional[float]
    margin_percentage: Optional[float]
    currency: str


class PrecursiveClient:
    """Client for interacting with Precursive data via Salesforce API."""
    
    def __init__(self, settings: Settings):
        # OAuth credentials
        self.client_id = settings.precursive_client_id
        self.client_secret = settings.precursive_client_secret
        self.instance_url = settings.precursive_instance_url.rstrip("/") if settings.precursive_instance_url else ""
        
        # Username/Password flow credentials (alternative)
        self.username = settings.precursive_username
        self.password = settings.precursive_password
        self.security_token = settings.precursive_security_token
        
        self._token: Optional[SalesforceToken] = None
        self._client: Optional[httpx.AsyncClient] = None
    
    @property
    def is_configured(self) -> bool:
        """Check if Salesforce credentials are configured."""
        # Check OAuth flow
        oauth_configured = bool(
            self.client_id and 
            self.client_secret and 
            self.instance_url
        )
        
        # Check Username/Password flow
        password_configured = bool(
            self.username and 
            self.password and 
            self.instance_url
        )
        
        return oauth_configured or password_configured
    
    @property
    def _uses_password_flow(self) -> bool:
        """Check if using username/password authentication."""
        return bool(self.username and self.password)
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client with authentication."""
        if self._client is None or self._client.is_closed:
            # Ensure we have a valid token
            if self._token is None:
                await self._authenticate()
            
            self._client = httpx.AsyncClient(
                base_url=self._token.instance_url,
                timeout=30.0,
                headers={
                    "Authorization": f"Bearer {self._token.access_token}",
                    "Content-Type": "application/json",
                }
            )
        return self._client
    
    async def close(self):
        """Close the HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
    
    async def _authenticate(self):
        """Authenticate with Salesforce and get access token."""
        if not self.is_configured:
            raise IntegrationError(
                "Precursive/Salesforce is not configured. "
                "Set PRECURSIVE_INSTANCE_URL and either OAuth or Username/Password credentials."
            )
        
        login_url = "https://login.salesforce.com/services/oauth2/token"
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                if self._uses_password_flow:
                    # Username/Password flow
                    response = await client.post(
                        login_url,
                        data={
                            "grant_type": "password",
                            "client_id": self.client_id or "3MVG9pRzvMkjMb6l9rMJ3vFmKhA3qCFnRLrP.NDc5EoJLjPaV_3kYKwO8ongpLBz3VvGVy0S.O.EvfQCU0Waw",  # Default connected app
                            "client_secret": self.client_secret or "",
                            "username": self.username,
                            "password": f"{self.password}{self.security_token}",
                        }
                    )
                else:
                    # Client credentials flow (for server-to-server)
                    response = await client.post(
                        login_url,
                        data={
                            "grant_type": "client_credentials",
                            "client_id": self.client_id,
                            "client_secret": self.client_secret,
                        }
                    )
                
                if response.status_code != 200:
                    error_data = response.json() if response.content else {}
                    error_msg = error_data.get("error_description", response.text)
                    raise IntegrationError(
                        f"Salesforce authentication failed: {error_msg}"
                    )
                
                data = response.json()
                self._token = SalesforceToken(
                    access_token=data["access_token"],
                    instance_url=data.get("instance_url", self.instance_url),
                    token_type=data.get("token_type", "Bearer"),
                    issued_at=datetime.now(),
                )
        except httpx.ConnectError as e:
            raise IntegrationError(f"Cannot connect to Salesforce: {str(e)}")
        except httpx.TimeoutException:
            raise IntegrationError("Salesforce authentication timed out")
    
    async def test_connection(self) -> dict:
        """
        Test the Salesforce connection and return user info.
        Raises IntegrationError if connection fails.
        """
        if not self.is_configured:
            raise IntegrationError(
                "Precursive/Salesforce is not configured. "
                "Set PRECURSIVE_INSTANCE_URL and credentials."
            )
        
        try:
            client = await self._get_client()
            response = await client.get("/services/data/v59.0/sobjects/")
            
            if response.status_code == 401:
                # Token expired, try to re-authenticate
                self._token = None
                self._client = None
                await self._authenticate()
                client = await self._get_client()
                response = await client.get("/services/data/v59.0/sobjects/")
            
            if response.status_code != 200:
                raise IntegrationError(
                    f"Salesforce connection failed: {response.status_code} - {response.text}"
                )
            
            return {
                "status": "connected",
                "instance_url": self._token.instance_url if self._token else "unknown",
                "api_version": "v59.0",
            }
        except httpx.HTTPError as e:
            raise IntegrationError(f"Salesforce API error: {str(e)}")
    
    async def get_precursive_projects(self, limit: int = 100) -> list[PrecursiveProject]:
        """
        Fetch Precursive projects from Salesforce.
        
        Note: This queries the preempt__PrecursiveProject__c custom object.
        """
        if not self.is_configured:
            raise IntegrationError("Precursive/Salesforce is not configured.")
        
        try:
            client = await self._get_client()
            
            # SOQL query for Precursive projects
            query = """
                SELECT Id, Name, preempt__Status__c, preempt__DeliveryPhase__c,
                       preempt__ProjectType__c, preempt__StartDate__c, 
                       preempt__EndDate__c, preempt__Account__r.Name
                FROM preempt__PrecursiveProject__c
                ORDER BY CreatedDate DESC
                LIMIT {limit}
            """.format(limit=limit).strip().replace("\n", " ")
            
            response = await client.get(
                "/services/data/v59.0/query/",
                params={"q": query}
            )
            
            if response.status_code == 400:
                # Object might not exist or different field names
                error_data = response.json()
                raise IntegrationError(
                    f"Salesforce query error: {error_data.get('message', response.text)}"
                )
            elif response.status_code != 200:
                raise IntegrationError(
                    f"Failed to fetch Precursive projects: {response.status_code}"
                )
            
            data = response.json()
            projects = []
            
            for record in data.get("records", []):
                account = record.get("preempt__Account__r") or {}
                projects.append(PrecursiveProject(
                    id=record["Id"],
                    name=record.get("Name", "Unknown"),
                    status=record.get("preempt__Status__c", "Unknown"),
                    delivery_phase=record.get("preempt__DeliveryPhase__c"),
                    project_type=record.get("preempt__ProjectType__c"),
                    start_date=record.get("preempt__StartDate__c"),
                    end_date=record.get("preempt__EndDate__c"),
                    client_name=account.get("Name"),
                ))
            
            return projects
        except httpx.HTTPError as e:
            raise IntegrationError(f"Salesforce API error: {str(e)}")
    
    async def get_project_financials(self, project_id: str) -> PrecursiveFinancials:
        """
        Fetch financial data for a Precursive project.
        
        Note: Field names may vary based on your Salesforce configuration.
        """
        if not self.is_configured:
            raise IntegrationError("Precursive/Salesforce is not configured.")
        
        try:
            client = await self._get_client()
            
            # SOQL query for project financials
            query = f"""
                SELECT Id, preempt__TotalBudget__c, preempt__SpentBudget__c,
                       preempt__RemainingBudget__c, preempt__Revenue__c,
                       preempt__MarginPercentage__c, CurrencyIsoCode
                FROM preempt__PrecursiveProject__c
                WHERE Id = '{project_id}'
            """.strip().replace("\n", " ")
            
            response = await client.get(
                "/services/data/v59.0/query/",
                params={"q": query}
            )
            
            if response.status_code != 200:
                raise IntegrationError(
                    f"Failed to fetch project financials: {response.status_code}"
                )
            
            data = response.json()
            records = data.get("records", [])
            
            if not records:
                raise IntegrationError(f"Project {project_id} not found in Salesforce")
            
            record = records[0]
            return PrecursiveFinancials(
                project_id=record["Id"],
                total_budget=record.get("preempt__TotalBudget__c"),
                spent_budget=record.get("preempt__SpentBudget__c"),
                remaining_budget=record.get("preempt__RemainingBudget__c"),
                revenue=record.get("preempt__Revenue__c"),
                margin_percentage=record.get("preempt__MarginPercentage__c"),
                currency=record.get("CurrencyIsoCode", "USD"),
            )
        except httpx.HTTPError as e:
            raise IntegrationError(f"Salesforce API error: {str(e)}")
    
    async def get_project_by_url(self, precursive_url: str) -> Optional[PrecursiveProject]:
        """
        Fetch a Precursive project by its Salesforce URL.
        
        Extracts the record ID from the URL and fetches the project.
        """
        if not self.is_configured:
            raise IntegrationError("Precursive/Salesforce is not configured.")
        
        # Extract record ID from URL
        # URL format: https://cognite.lightning.force.com/lightning/r/preempt__PrecursiveProject__c/a2XSZ000000p3a92AA/view
        import re
        match = re.search(r'/([a-zA-Z0-9]{15,18})(?:/|$)', precursive_url)
        
        if not match:
            raise IntegrationError(f"Could not extract Salesforce ID from URL: {precursive_url}")
        
        record_id = match.group(1)
        
        try:
            client = await self._get_client()
            
            query = f"""
                SELECT Id, Name, preempt__Status__c, preempt__DeliveryPhase__c,
                       preempt__ProjectType__c, preempt__StartDate__c, 
                       preempt__EndDate__c, preempt__Account__r.Name
                FROM preempt__PrecursiveProject__c
                WHERE Id = '{record_id}'
            """.strip().replace("\n", " ")
            
            response = await client.get(
                "/services/data/v59.0/query/",
                params={"q": query}
            )
            
            if response.status_code != 200:
                raise IntegrationError(
                    f"Failed to fetch project: {response.status_code}"
                )
            
            data = response.json()
            records = data.get("records", [])
            
            if not records:
                return None
            
            record = records[0]
            account = record.get("preempt__Account__r") or {}
            return PrecursiveProject(
                id=record["Id"],
                name=record.get("Name", "Unknown"),
                status=record.get("preempt__Status__c", "Unknown"),
                delivery_phase=record.get("preempt__DeliveryPhase__c"),
                project_type=record.get("preempt__ProjectType__c"),
                start_date=record.get("preempt__StartDate__c"),
                end_date=record.get("preempt__EndDate__c"),
                client_name=account.get("Name"),
            )
        except httpx.HTTPError as e:
            raise IntegrationError(f"Salesforce API error: {str(e)}")

