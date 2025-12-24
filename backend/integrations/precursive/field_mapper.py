"""Field mapper for converting Salesforce API responses to dataclasses.

This module provides the Anti-Corruption Layer (ACL) between the raw
Salesforce API responses and our domain models. It handles:
- Field name mapping using schema constants
- Null handling for optional fields
- Type conversion where needed
- Relationship traversal (e.g., Account.Name)
"""

from typing import Any, Dict

from .models import PrecursiveFinancials, PrecursiveProject
from .salesforce_schema import PrecursiveProjectFields as F


def map_salesforce_to_project(raw: Dict[str, Any]) -> PrecursiveProject:
    """Map raw Salesforce response to PrecursiveProject dataclass.

    Args:
        raw: Raw dictionary from Salesforce API query response

    Returns:
        PrecursiveProject dataclass with mapped fields
    """
    # Handle relationship traversal for Account name
    account = raw.get("preempt__account__r") or {}
    client_name = account.get("Name") if isinstance(account, dict) else None

    return PrecursiveProject(
        # Core fields
        id=raw[F.ID],
        name=raw.get(F.NAME, ""),
        status=raw.get(F.STATUS),
        project_category=raw.get(F.PROJECT_CATEGORY),
        # Dates
        delivery_start_date=raw.get(F.DELIVERY_START),
        delivery_end_date=raw.get(F.DELIVERY_END),
        # Client
        client_name=client_name,
        # Health indicators
        project_health=raw.get(F.PROJECT_STATUS),
        time_health=raw.get(F.TIME_STATUS),
        cost_health=raw.get(F.COST_STATUS),
        resources_health=raw.get(F.RESOURCES_STATUS),
        # Status summary
        overall_status_summary=raw.get(F.OVERALL_STATUS_SUMMARY),
        # Embedded risk
        risk_level=raw.get(F.RISK_LEVEL),
        risk_description=raw.get(F.RISK_DESCRIPTION),
    )


def map_salesforce_to_financials(
    project_id: str, raw: Dict[str, Any]
) -> PrecursiveFinancials:
    """Map raw Salesforce response to PrecursiveFinancials dataclass.

    Args:
        project_id: The project ID to associate with these financials
        raw: Raw dictionary from Salesforce API query response

    Returns:
        PrecursiveFinancials dataclass with mapped fields
    """
    return PrecursiveFinancials(
        project_id=project_id,
        currency=raw.get(F.CURRENCY, "USD"),
        # Core financial fields
        remaining_budget=raw.get(F.REMAINING_BUDGET),
        remaining_budget_org=raw.get(F.REMAINING_BUDGET_ORG),
        total_fte_days=raw.get(F.TOTAL_FTE_DAYS),
        fte_day_price=raw.get(F.FTE_DAY_PRICE),
        overrun_investment=raw.get(F.OVERRUN_INVESTMENT),
        overrun_investment_diff=raw.get(F.OVERRUN_INVESTMENT_DIFF),
        budgeted_days_delivery=raw.get(F.BUDGETED_DAYS_DELIVERY),
        budgeted_hours_delivery=raw.get(F.BUDGETED_HOURS_DELIVERY),
        total_days_actuals_planned=raw.get(F.TOTAL_DAYS_ACTUALS_PLANNED),
        # Budget breakdown by role (in days)
        pm_budget=raw.get(F.PM_BUDGET),
        sa_budget=raw.get(F.SA_BUDGET),
        de_budget=raw.get(F.DE_BUDGET),
        ds_budget=raw.get(F.DS_BUDGET),
        # Budgeted FTE by role
        pm_budgeted_fte=raw.get(F.PM_BUDGETED_FTE),
        sa_budgeted_fte=raw.get(F.SA_BUDGETED_FTE),
        de_budgeted_fte=raw.get(F.DE_BUDGETED_FTE),
        ds_budgeted_fte=raw.get(F.DS_BUDGETED_FTE),
        # Actual FTE by role
        pm_actual_fte=raw.get(F.PM_ACTUAL_FTE),
        sa_actual_fte=raw.get(F.SA_ACTUAL_FTE),
        de_actual_fte=raw.get(F.DE_ACTUAL_FTE),
        ds_actual_fte=raw.get(F.DS_ACTUAL_FTE),
        # FTE variance by role
        pm_fte_difference=raw.get(F.PM_FTE_DIFFERENCE),
        sa_fte_difference=raw.get(F.SA_FTE_DIFFERENCE),
        de_fte_difference=raw.get(F.DE_FTE_DIFFERENCE),
        ds_fte_difference=raw.get(F.DS_FTE_DIFFERENCE),
        # Mobilization phase
        mobilizing_total_fte_days=raw.get(F.MOBILIZING_TOTAL_FTE_DAYS),
        mobilizing_overrun=raw.get(F.MOBILIZING_OVERRUN),
    )
