"""Integrations package for external API clients."""

from integrations.jira_client import JiraClient, JiraIssue, JiraProject, JiraSprint
from integrations.precursive_client import (
    PrecursiveClient,
    PrecursiveFinancials,
    PrecursiveProject,
    SalesforceToken,
)

__all__ = [
    # Jira
    "JiraClient",
    "JiraProject",
    "JiraIssue",
    "JiraSprint",
    # Precursive/Salesforce
    "PrecursiveClient",
    "PrecursiveProject",
    "PrecursiveFinancials",
    "SalesforceToken",
]
