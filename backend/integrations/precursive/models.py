"""Dataclasses for Precursive/Salesforce data.

These dataclasses represent the domain model for Precursive data
after mapping from raw Salesforce API responses.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class PrecursiveProject:
    """Precursive project data with health indicators and embedded risk."""

    # Core fields
    id: str
    name: str
    status: Optional[str]  # Phase (Icebox, Defining, Delivery, etc.)
    project_category: Optional[str]

    # Dates
    delivery_start_date: Optional[str]
    delivery_end_date: Optional[str]

    # Client (from Account relationship)
    client_name: Optional[str]

    # Health Indicators (RAG status)
    project_health: Optional[str]  # On track, Minor deviations, Requires attention, N/A
    time_health: Optional[str]
    cost_health: Optional[str]
    resources_health: Optional[str]

    # Status Summary
    overall_status_summary: Optional[str]

    # Embedded Risk (project-level, not granular)
    risk_level: Optional[str]  # High, Medium, Low
    risk_description: Optional[str]


@dataclass
class PrecursiveFinancials:
    """Financial data extracted from Precursive project.

    Contains all available budget fields from Salesforce Precursive.
    Some projects may only have a subset of these fields populated.
    """

    project_id: str
    currency: str

    # Core budget/spending fields
    remaining_budget: Optional[float] = None
    remaining_budget_org: Optional[float] = None
    total_fte_days: Optional[float] = None
    fte_day_price: Optional[float] = None
    overrun_investment: Optional[float] = None
    overrun_investment_diff: Optional[float] = None  # Percentage
    budgeted_days_delivery: Optional[float] = None
    budgeted_hours_delivery: Optional[float] = None
    total_days_actuals_planned: Optional[float] = None

    # Budget breakdown by role (in days)
    pm_budget: Optional[float] = None
    sa_budget: Optional[float] = None
    de_budget: Optional[float] = None
    ds_budget: Optional[float] = None

    # Budgeted FTE by role
    pm_budgeted_fte: Optional[float] = None
    sa_budgeted_fte: Optional[float] = None
    de_budgeted_fte: Optional[float] = None
    ds_budgeted_fte: Optional[float] = None

    # Actual FTE by role
    pm_actual_fte: Optional[float] = None
    sa_actual_fte: Optional[float] = None
    de_actual_fte: Optional[float] = None
    ds_actual_fte: Optional[float] = None

    # FTE variance by role (percentage over/under)
    pm_fte_difference: Optional[float] = None
    sa_fte_difference: Optional[float] = None
    de_fte_difference: Optional[float] = None
    ds_fte_difference: Optional[float] = None

    # Mobilization phase
    mobilizing_total_fte_days: Optional[float] = None
    mobilizing_overrun: Optional[float] = None

    def compute_total_budget(self) -> Optional[float]:
        """Compute total budget using available data.

        Tries multiple strategies in order of reliability:
        1. FTE days × day price (if both available)
        2. Sum of role budgets × day price (if available)
        3. None if no data available

        Returns:
            Computed total budget in currency units, or None
        """
        # Strategy 1: Direct FTE calculation
        if self.total_fte_days is not None and self.fte_day_price is not None:
            computed = self.total_fte_days * self.fte_day_price
            if computed > 0:
                return computed

        # Strategy 2: Sum of role budgets (these are in days, need price)
        if self.fte_day_price is not None:
            role_days = sum(
                filter(
                    None,
                    [self.pm_budget, self.sa_budget, self.de_budget, self.ds_budget],
                )
            )
            if role_days > 0:
                return role_days * self.fte_day_price

        return None

    def compute_spent_budget(self) -> Optional[float]:
        """Compute spent budget from total minus remaining.

        Returns:
            Spent budget amount, or None if cannot be computed
        """
        total = self.compute_total_budget()
        if total is not None and self.remaining_budget is not None:
            return total - self.remaining_budget
        return None

    def has_any_financial_data(self) -> bool:
        """Check if any financial data is available."""
        return any(
            [
                self.remaining_budget,
                self.total_fte_days,
                self.fte_day_price,
                self.overrun_investment,
                self.pm_budget,
                self.sa_budget,
                self.de_budget,
                self.ds_budget,
                self.total_days_actuals_planned,
                self.pm_budgeted_fte,
                self.sa_budgeted_fte,
                self.de_budgeted_fte,
                self.ds_budgeted_fte,
                self.pm_actual_fte,
                self.sa_actual_fte,
                self.de_actual_fte,
                self.ds_actual_fte,
            ]
        )

    def get_total_budgeted_fte(self) -> Optional[float]:
        """Sum of all budgeted FTE across roles."""
        values = [
            self.pm_budgeted_fte,
            self.sa_budgeted_fte,
            self.de_budgeted_fte,
            self.ds_budgeted_fte,
        ]
        filtered = [v for v in values if v is not None]
        return sum(filtered) if filtered else None

    def get_total_actual_fte(self) -> Optional[float]:
        """Sum of all actual FTE across roles."""
        values = [
            self.pm_actual_fte,
            self.sa_actual_fte,
            self.de_actual_fte,
            self.ds_actual_fte,
        ]
        filtered = [v for v in values if v is not None]
        return sum(filtered) if filtered else None


@dataclass
class PrecursiveRisk:
    """Risk data for legacy mock compatibility.

    Note: In the real Salesforce schema, risks are embedded in the project
    via Project_Risk_Level__c and Risk_Description__c fields.
    This dataclass is kept for mock client compatibility.
    """

    summary: str
    description: str
    category: Optional[str]
    impact_rationale: Optional[str]
    date_identified: Optional[str]
    probability: str
    impact: str
    status: str
    mitigation_plan: Optional[str]
