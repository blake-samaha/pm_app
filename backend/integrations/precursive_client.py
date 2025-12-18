"""Mock Precursive client for development."""

import json
import os
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

from config import Settings


@dataclass
class SalesforceToken:
    """Mock Salesforce OAuth token data."""

    access_token: str
    instance_url: str
    token_type: str
    issued_at: datetime


@dataclass
class PrecursiveProject:
    """Precursive project data."""

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
    """Financial data."""

    project_id: str
    total_budget: Optional[float]
    spent_budget: Optional[float]
    remaining_budget: Optional[float]
    revenue: Optional[float]
    margin_percentage: Optional[float]
    currency: str


@dataclass
class PrecursiveRisk:
    """Risk data."""

    summary: str
    description: str
    category: Optional[str]
    impact_rationale: Optional[str]
    date_identified: Optional[str]
    probability: str
    impact: str
    status: str
    mitigation_plan: Optional[str]


class PrecursiveClient:
    """Mock client that reads from local JSON data."""

    def __init__(self, settings: Settings):
        self.settings = settings
        # Resolve path relative to this file
        self.data_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "data", "mock_precursive.json"
        )
        self._data = self._load_data()

    def _load_data(self) -> Dict[str, Any]:
        try:
            with open(self.data_path, "r") as f:
                return json.load(f)
        except FileNotFoundError:
            return {"projects": []}

    @property
    def is_configured(self) -> bool:
        """Always return True for mock."""
        return True

    async def close(self):
        pass

    async def test_connection(self) -> dict:
        return {
            "status": "connected",
            "type": "mock",
            "project_count": len(self._data.get("projects", [])),
        }

    async def get_project_by_id(self, project_id: str) -> Optional[PrecursiveProject]:
        """Find project by ID in mock data."""
        for p in self._data.get("projects", []):
            if p.get("id") == project_id:
                return self._map_project(p)
        return None

    async def get_project_by_url(
        self, precursive_url: str
    ) -> Optional[PrecursiveProject]:
        """Find project by URL in mock data."""
        # Only return exact match - no fallback to prevent data contamination
        if precursive_url:
            for p in self._data.get("projects", []):
                if p.get("precursive_url") == precursive_url:
                    return self._map_project(p)

        return None

    def _map_project(self, p: Dict[str, Any]) -> PrecursiveProject:
        return PrecursiveProject(
            id=p["id"],
            name=p["name"],
            status=p["status"],
            delivery_phase=p.get("delivery_phase"),
            project_type=p.get("project_type"),
            start_date=p.get("start_date"),
            end_date=p.get("end_date"),
            client_name=p.get("client_name"),
        )

    async def get_project_financials(self, project_id: str) -> PrecursiveFinancials:
        """Get financials from mock data."""
        # Only return exact match - no fallback to prevent data contamination
        for p in self._data.get("projects", []):
            if p["id"] == project_id:
                fin = p.get("financials", {})
                return PrecursiveFinancials(
                    project_id=project_id,
                    total_budget=fin.get("total_budget"),
                    spent_budget=fin.get("spent_budget"),
                    remaining_budget=fin.get("remaining_budget"),
                    revenue=fin.get("revenue"),
                    margin_percentage=fin.get("margin_percentage"),
                    currency=fin.get("currency", "USD"),
                )

        # Return empty/zero financials if no match found
        return PrecursiveFinancials(project_id, 0, 0, 0, 0, 0, "USD")

    async def get_project_risks(self, project_id: str) -> List[PrecursiveRisk]:
        """Get risks from mock data."""
        risks = []
        # Only return exact match - no fallback to prevent data contamination
        for p in self._data.get("projects", []):
            if p["id"] == project_id:
                for r in p.get("risks", []):
                    risks.append(
                        PrecursiveRisk(
                            summary=r["summary"],
                            description=r["description"],
                            category=r.get("category"),
                            impact_rationale=r.get("impact_rationale"),
                            date_identified=r.get("date_identified"),
                            probability=r["probability"],
                            impact=r["impact"],
                            status=r["status"],
                            mitigation_plan=r.get("mitigation_plan"),
                        )
                    )
                return risks

        return risks
