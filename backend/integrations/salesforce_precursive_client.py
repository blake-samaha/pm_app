"""Precursive/Salesforce API client for fetching project data."""

import asyncio
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

import httpx
import structlog

from config import Settings
from exceptions import IntegrationError

from .precursive import (
    PrecursiveFinancials,
    PrecursiveProject,
    map_salesforce_to_financials,
    map_salesforce_to_project,
)
from .precursive import (
    PrecursiveProjectFields as F,
)
from .precursive.models import PrecursiveRisk

logger = structlog.get_logger()


@dataclass
class SalesforceToken:
    """Salesforce OAuth token data."""

    access_token: str
    instance_url: str
    token_type: str
    issued_at: datetime


class SalesforcePrecursiveClient:
    """Client for interacting with Precursive/Salesforce API using OAuth client credentials flow."""

    # Salesforce API version - centralized for easy updates
    API_VERSION = "v59.0"

    # Regex pattern for valid Salesforce IDs (15 or 18 alphanumeric characters)
    _SALESFORCE_ID_PATTERN = re.compile(r"^[a-zA-Z0-9]{15,18}$")

    def __init__(self, settings: Settings):
        self.settings = settings
        self.client_id = (
            settings.precursive_client_id.strip()
            if settings.precursive_client_id
            else ""
        )
        self.client_secret = (
            settings.precursive_client_secret.strip()
            if settings.precursive_client_secret
            else ""
        )
        self.instance_url = (
            settings.precursive_instance_url.strip().rstrip("/")
            if settings.precursive_instance_url
            else ""
        )
        self._client: Optional[httpx.AsyncClient] = None
        self._token: Optional[SalesforceToken] = None
        self._auth_lock = asyncio.Lock()

    @property
    def is_configured(self) -> bool:
        """Check if Precursive/Salesforce credentials are configured."""
        return bool(self.client_id and self.client_secret)

    def _validate_salesforce_id(self, sf_id: str) -> str:
        """Validate Salesforce ID format to prevent SOQL injection.

        Salesforce IDs are 15 or 18 alphanumeric characters.

        Args:
            sf_id: The Salesforce ID to validate.

        Returns:
            The validated ID (unchanged).

        Raises:
            IntegrationError: If the ID format is invalid.
        """
        if not sf_id or not self._SALESFORCE_ID_PATTERN.match(sf_id):
            # Truncate ID in error message to avoid log injection
            display_id = sf_id[:20] if sf_id else "empty"
            raise IntegrationError(f"Invalid Salesforce ID format: {display_id}")
        return sf_id

    def _get_token_url(self) -> str:
        """Determine the appropriate token URL based on instance URL."""
        if self.instance_url:
            if "lightning.force.com" in self.instance_url:
                # Extract domain: cognite.lightning.force.com -> cognite
                parts = self.instance_url.replace("https://", "").split(".")
                if parts:
                    domain = parts[0]
                    return f"https://{domain}.my.salesforce.com/services/oauth2/token"
            elif "my.salesforce.com" in self.instance_url:
                host = self.instance_url.replace("https://", "").split("/")[0]
                return f"https://{host}/services/oauth2/token"
        # Fallback to generic login URL
        return "https://login.salesforce.com/services/oauth2/token"

    async def _authenticate(self) -> SalesforceToken:
        """Authenticate with Salesforce using client credentials flow."""
        token_url = self._get_token_url()

        payload = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }
        headers = {"Content-Type": "application/x-www-form-urlencoded"}

        logger.info("Authenticating with Salesforce", token_url=token_url)

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(token_url, data=payload, headers=headers)

                if response.status_code == 401:
                    raise IntegrationError(
                        "Salesforce authentication failed. Check your client credentials."
                    )
                elif response.status_code == 400:
                    try:
                        error_data = response.json()
                        error_desc = error_data.get("error_description", response.text)
                    except ValueError:
                        error_desc = response.text
                    raise IntegrationError(f"Salesforce OAuth error: {error_desc}")

                response.raise_for_status()
                data = response.json()

                logger.info(
                    "Salesforce authentication successful",
                    instance_url=data.get("instance_url"),
                )

                return SalesforceToken(
                    access_token=data["access_token"],
                    instance_url=data["instance_url"],
                    token_type=data.get("token_type", "Bearer"),
                    issued_at=datetime.now(),
                )
        except httpx.ConnectError as e:
            raise IntegrationError(f"Cannot connect to Salesforce: {str(e)}") from e
        except httpx.TimeoutException as e:
            raise IntegrationError("Salesforce connection timed out") from e
        except httpx.HTTPStatusError as e:
            raise IntegrationError(
                f"Salesforce authentication failed: {e.response.status_code}"
            ) from e

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create authenticated HTTP client."""
        if self._token is None:
            self._token = await self._authenticate()

        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self._token.instance_url,
                timeout=30.0,
                headers={
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self._token.access_token}",
                },
            )
        return self._client

    async def close(self):
        """Close the HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    async def test_connection(self) -> dict:
        """Test the Salesforce connection."""
        if not self.is_configured:
            raise IntegrationError(
                "Precursive is not configured. Set PRECURSIVE_CLIENT_ID and PRECURSIVE_CLIENT_SECRET."
            )

        try:
            client = await self._get_client()
            # Query API version endpoint to verify connection
            response = await client.get(f"/services/data/{self.API_VERSION}/")

            if response.status_code != 200:
                raise IntegrationError(
                    f"Salesforce API error: {response.status_code} - {response.text}"
                )

            return {
                "status": "connected",
                "type": "salesforce",
                "instance_url": self._token.instance_url if self._token else "unknown",
            }
        except httpx.HTTPError as e:
            raise IntegrationError(f"Salesforce API error: {str(e)}") from e

    async def _query(self, soql: str) -> List[Dict[str, Any]]:
        """Execute a SOQL query and return records."""
        client = await self._get_client()
        query_url = f"/services/data/{self.API_VERSION}/query"
        response = await client.get(query_url, params={"q": soql})

        if response.status_code == 401:
            # Token might have expired, try re-authenticating with lock
            # to prevent multiple concurrent requests from racing
            async with self._auth_lock:
                # Double-check in case another request already refreshed
                if (
                    self._token is None
                    or self._client is None
                    or self._client.is_closed
                ):
                    self._token = None
                    self._client = None
                    client = await self._get_client()

            response = await client.get(query_url, params={"q": soql})

        if response.status_code != 200:
            raise IntegrationError(
                f"Salesforce query failed: {response.status_code} - {response.text}"
            )

        data = response.json()
        return data.get("records", [])

    def _build_project_query(self, where_clause: str) -> str:
        """Build SOQL query for project with all sync fields."""
        fields = ", ".join(F.all_sync_fields())
        return f"SELECT {fields} FROM {F.SOBJECT} WHERE {where_clause}"

    async def get_project_by_id(self, project_id: str) -> Optional[PrecursiveProject]:
        """Fetch a Precursive project by Salesforce ID."""
        if not self.is_configured:
            raise IntegrationError("Precursive is not configured.")

        try:
            validated_id = self._validate_salesforce_id(project_id)
            soql = self._build_project_query(f"Id = '{validated_id}'")
            logger.debug("Executing SOQL query", soql=soql)

            records = await self._query(soql)

            if not records:
                logger.warning("Project not found in Precursive", project_id=project_id)
                return None

            return map_salesforce_to_project(records[0])
        except httpx.HTTPError as e:
            raise IntegrationError(f"Salesforce API error: {str(e)}") from e

    async def get_project_by_url(
        self, precursive_url: str
    ) -> Optional[PrecursiveProject]:
        """Find project by Precursive URL."""
        if not self.is_configured:
            raise IntegrationError("Precursive is not configured.")

        if not precursive_url:
            return None

        # Extract Salesforce ID from URL
        # Common formats:
        # - https://cognite.lightning.force.com/lightning/r/preempt__PrecursiveProject__c/a2X.../view
        # - https://cognite.my.salesforce.com/a2X...
        project_id = None

        # Try Precursive object URL format first
        if "/r/preempt__PrecursiveProject__c/" in precursive_url:
            # Lightning URL format for Precursive projects
            parts = precursive_url.split("/r/preempt__PrecursiveProject__c/")
            if len(parts) > 1:
                project_id = parts[1].split("/")[0]
        elif "/r/pse__Proj__c/" in precursive_url:
            # Legacy PSA/FinancialForce URL format (fallback)
            parts = precursive_url.split("/r/pse__Proj__c/")
            if len(parts) > 1:
                project_id = parts[1].split("/")[0]
        elif "my.salesforce.com/" in precursive_url:
            # Classic URL format - extract last path segment
            parts = precursive_url.rstrip("/").split("/")
            if parts:
                potential_id = parts[-1]
                # Salesforce IDs are 15 or 18 characters
                if len(potential_id) in (15, 18) and potential_id.isalnum():
                    project_id = potential_id

        if project_id:
            return await self.get_project_by_id(project_id)

        logger.warning("Could not extract project ID from URL", url=precursive_url)
        return None

    async def get_project_financials(self, project_id: str) -> PrecursiveFinancials:
        """Get financial data for a project from Salesforce."""
        if not self.is_configured:
            raise IntegrationError("Precursive is not configured.")

        try:
            validated_id = self._validate_salesforce_id(project_id)
            # Query all financial fields
            fields = ", ".join([F.ID] + F.financial_fields())
            soql = f"SELECT {fields} FROM {F.SOBJECT} WHERE Id = '{validated_id}'"

            logger.debug(
                "Fetching Precursive financials",
                project_id=project_id,
                fields_requested=F.financial_fields(),
            )

            records = await self._query(soql)

            if not records:
                logger.warning(
                    "No financial records found in Salesforce",
                    project_id=project_id,
                )
                return PrecursiveFinancials(project_id=project_id, currency="USD")

            # Log raw response for debugging - core fields
            raw_data = records[0]
            logger.info(
                "Precursive financials - core data",
                project_id=project_id,
                currency=raw_data.get(F.CURRENCY),
                total_fte_days=raw_data.get(F.TOTAL_FTE_DAYS),
                fte_day_price=raw_data.get(F.FTE_DAY_PRICE),
                remaining_budget=raw_data.get(F.REMAINING_BUDGET),
                overrun_investment=raw_data.get(F.OVERRUN_INVESTMENT),
                total_days_actuals_planned=raw_data.get(F.TOTAL_DAYS_ACTUALS_PLANNED),
            )

            # Log role budgets
            logger.info(
                "Precursive financials - role budgets (days)",
                project_id=project_id,
                pm_budget=raw_data.get(F.PM_BUDGET),
                sa_budget=raw_data.get(F.SA_BUDGET),
                de_budget=raw_data.get(F.DE_BUDGET),
                ds_budget=raw_data.get(F.DS_BUDGET),
            )

            # Log FTE tracking
            logger.info(
                "Precursive financials - FTE tracking",
                project_id=project_id,
                pm_budgeted_fte=raw_data.get(F.PM_BUDGETED_FTE),
                sa_budgeted_fte=raw_data.get(F.SA_BUDGETED_FTE),
                de_budgeted_fte=raw_data.get(F.DE_BUDGETED_FTE),
                ds_budgeted_fte=raw_data.get(F.DS_BUDGETED_FTE),
                pm_actual_fte=raw_data.get(F.PM_ACTUAL_FTE),
                sa_actual_fte=raw_data.get(F.SA_ACTUAL_FTE),
                de_actual_fte=raw_data.get(F.DE_ACTUAL_FTE),
                ds_actual_fte=raw_data.get(F.DS_ACTUAL_FTE),
            )

            financials = map_salesforce_to_financials(project_id, raw_data)

            # Log computed values
            computed_total = financials.compute_total_budget()
            computed_spent = financials.compute_spent_budget()
            logger.info(
                "Precursive financials - computed values",
                project_id=project_id,
                computed_total_budget=computed_total,
                computed_spent_budget=computed_spent,
                has_any_data=financials.has_any_financial_data(),
            )

            return financials
        except httpx.HTTPError as e:
            logger.warning("Failed to fetch financials from Salesforce", error=str(e))
            return PrecursiveFinancials(project_id=project_id, currency="USD")

    async def get_project_risks(self, project_id: str) -> List[PrecursiveRisk]:
        """Get risks for a project from Salesforce.

        Note: In Precursive, risks are embedded in the project object as
        Project_Risk_Level__c and Risk_Description__c fields. This method
        returns an empty list since there's no separate risk object.
        The project-level risk is extracted during project sync instead.
        """
        if not self.is_configured:
            raise IntegrationError("Precursive is not configured.")

        # Precursive doesn't have a separate risk object - risks are embedded
        # in the project. Return empty list for backward compatibility.
        # The project-level risk (Project_Risk_Level__c, Risk_Description__c)
        # is handled during the sync_precursive_data flow.
        logger.debug(
            "get_project_risks called - returning empty list (risks are embedded in project)",
            project_id=project_id,
        )
        return []
