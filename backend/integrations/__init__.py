"""Integrations package for external API clients."""

from integrations.jira_client import JiraClient, JiraIssue, JiraProject, JiraSprint
from integrations.precursive import (
    PrecursiveFinancials,
    PrecursiveProject,
    PrecursiveProjectFields,
    PrecursiveRisk,
)
from integrations.salesforce_precursive_client import (
    SalesforcePrecursiveClient,
    SalesforceToken,
)

__all__ = [
    # Jira
    "JiraClient",
    "JiraProject",
    "JiraIssue",
    "JiraSprint",
    # Precursive/Salesforce
    "PrecursiveProjectFields",
    "SalesforcePrecursiveClient",
    "PrecursiveProject",
    "PrecursiveFinancials",
    "PrecursiveRisk",
    "SalesforceToken",
]
