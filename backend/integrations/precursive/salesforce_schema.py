"""Salesforce schema constants for Precursive objects.

This module centralizes all Salesforce field names to:
- Prevent typos in SOQL queries
- Make schema changes easy to propagate
- Enable IDE autocomplete
"""

from typing import List


class PrecursiveProjectFields:
    """Field constants for preempt__PrecursiveProject__c Salesforce object."""

    # Salesforce object name
    SOBJECT = "preempt__PrecursiveProject__c"

    # Core fields
    ID = "Id"
    NAME = "Name"
    STATUS = "preempt__Status__c"  # Phase picklist (Icebox, Defining, Delivery, etc.)
    PROJECT_CATEGORY = "preempt__projectCategory__c"
    ACCOUNT_ID = "preempt__account__c"

    # Relationship fields (for SOQL relationship queries)
    ACCOUNT_NAME = "preempt__account__r.Name"

    # Date fields
    DELIVERY_START = "Delivery_Start_Date__c"
    DELIVERY_END = "Delivery_End_Date__c"

    # Health/RAG indicator picklists (On track, Minor deviations, Requires attention, N/A)
    PROJECT_STATUS = "Project_Status_Pick__c"
    TIME_STATUS = "Time_Status_Pick__c"
    COST_STATUS = "Cost_Status_Pick__c"
    RESOURCES_STATUS = "Resources_Status_Pick__c"

    # Status Comments/Summary fields
    OVERALL_STATUS_SUMMARY = "Scope_Comments2__c"
    PROJECT_STATUS_COMMENTS = "LT_Comments__c"
    COST_COMMENTS = "Cost_Comments2__c"
    TIME_COMMENTS = "Time_Comments2__c"
    RESOURCES_COMMENTS = "Resources_Comments2__c"

    # Financial fields - Core
    CURRENCY = "CurrencyIsoCode"
    REMAINING_BUDGET = "Remaining_Budget__c"
    FTE_DAY_PRICE = "FTE_Day_Price__c"
    TOTAL_FTE_DAYS = "Total_FTEs__c"
    OVERRUN_INVESTMENT = "Overrun_Investment__c"
    BUDGETED_DAYS_DELIVERY = "Budgeted_Days_in_Delivery_Phase__c"
    BUDGETED_HOURS_DELIVERY = "Budgeted_Hours_in_Delivery_Phase__c"

    # Financial fields - Extended budget breakdown by role (in days)
    PM_BUDGET = "PM_Budget__c"
    SA_BUDGET = "SA_Budget__c"
    DE_BUDGET = "DE_Budget__c"
    DS_BUDGET = "DS_Budget__c"
    TOTAL_DAYS_ACTUALS_PLANNED = "Total_Days_Actuals_Planned__c"
    REMAINING_BUDGET_ORG = "Remaining_Budget_in_Fees_org__c"
    OVERRUN_INVESTMENT_DIFF = "Overrun_Investment_Diff__c"

    # FTE tracking - Budgeted by role
    PM_BUDGETED_FTE = "PM_Budgeted_FTE__c"
    SA_BUDGETED_FTE = "SA_Budgeted_FTE__c"
    DE_BUDGETED_FTE = "DE_Budgeted_FTE__c"
    DS_BUDGETED_FTE = "DS_Budgeted_FTE__c"

    # FTE tracking - Actual by role
    PM_ACTUAL_FTE = "PM_Actual_FTE__c"
    SA_ACTUAL_FTE = "SA_Actual_FTE__c"
    DE_ACTUAL_FTE = "DE_Actual_FTE__c"
    DS_ACTUAL_FTE = "DS_Actual_FTE__c"

    # FTE tracking - Variance by role (percentage)
    PM_FTE_DIFFERENCE = "PM_FTE_Difference__c"
    SA_FTE_DIFFERENCE = "SA_FTE_Difference__c"
    DE_FTE_DIFFERENCE = "DE_FTE_Difference__c"
    DS_FTE_DIFFERENCE = "DS_FTE_Difference__c"

    # Mobilization phase financials
    MOBILIZING_TOTAL_FTE_DAYS = "Mobilizing_Total_FTE_Days__c"
    MOBILIZING_OVERRUN = "Mobilizing_Overrun__c"

    # Risk fields (embedded in project, not separate object)
    RISK_LEVEL = "Project_Risk_Level__c"  # Picklist: High, Medium, Low
    RISK_DESCRIPTION = "Risk_Description__c"

    # Metadata fields
    LAST_MODIFIED_DATE = "LastModifiedDate"
    LAST_STATUS_UPDATE = "Last_Project_Status_Update2__c"
    STATUS_UPDATED_BY = "Project_Status_Last_Updated_By__c"

    # Field sets for different query types
    @classmethod
    def core_fields(cls) -> List[str]:
        """Fields needed for basic project identification."""
        return [
            cls.ID,
            cls.NAME,
            cls.STATUS,
            cls.PROJECT_CATEGORY,
            cls.ACCOUNT_NAME,
        ]

    @classmethod
    def date_fields(cls) -> List[str]:
        """Date fields for timeline."""
        return [
            cls.DELIVERY_START,
            cls.DELIVERY_END,
        ]

    @classmethod
    def health_fields(cls) -> List[str]:
        """Health/RAG status indicator fields."""
        return [
            cls.PROJECT_STATUS,
            cls.TIME_STATUS,
            cls.COST_STATUS,
            cls.RESOURCES_STATUS,
            cls.OVERALL_STATUS_SUMMARY,
        ]

    @classmethod
    def financial_fields(cls) -> List[str]:
        """Financial data fields - all available budget/spending fields."""
        return [
            # Core financial fields
            cls.CURRENCY,
            cls.REMAINING_BUDGET,
            cls.REMAINING_BUDGET_ORG,
            cls.FTE_DAY_PRICE,
            cls.TOTAL_FTE_DAYS,
            cls.OVERRUN_INVESTMENT,
            cls.OVERRUN_INVESTMENT_DIFF,
            cls.BUDGETED_DAYS_DELIVERY,
            cls.BUDGETED_HOURS_DELIVERY,
            cls.TOTAL_DAYS_ACTUALS_PLANNED,
            # Budget breakdown by role (in days)
            cls.PM_BUDGET,
            cls.SA_BUDGET,
            cls.DE_BUDGET,
            cls.DS_BUDGET,
            # Budgeted FTE by role
            cls.PM_BUDGETED_FTE,
            cls.SA_BUDGETED_FTE,
            cls.DE_BUDGETED_FTE,
            cls.DS_BUDGETED_FTE,
            # Actual FTE by role
            cls.PM_ACTUAL_FTE,
            cls.SA_ACTUAL_FTE,
            cls.DE_ACTUAL_FTE,
            cls.DS_ACTUAL_FTE,
            # FTE variance by role
            cls.PM_FTE_DIFFERENCE,
            cls.SA_FTE_DIFFERENCE,
            cls.DE_FTE_DIFFERENCE,
            cls.DS_FTE_DIFFERENCE,
            # Mobilization phase
            cls.MOBILIZING_TOTAL_FTE_DAYS,
            cls.MOBILIZING_OVERRUN,
        ]

    @classmethod
    def risk_fields(cls) -> List[str]:
        """Embedded risk fields."""
        return [
            cls.RISK_LEVEL,
            cls.RISK_DESCRIPTION,
        ]

    @classmethod
    def all_sync_fields(cls) -> List[str]:
        """All fields needed for a full project sync."""
        return (
            cls.core_fields()
            + cls.date_fields()
            + cls.health_fields()
            + cls.financial_fields()
            + cls.risk_fields()
        )
