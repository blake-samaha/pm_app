"""Integrations package for external API clients."""
from integrations.jira_client import JiraClient, JiraProject, JiraIssue, JiraSprint
from integrations.precursive_client import (
    PrecursiveClient, 
    PrecursiveProject, 
    PrecursiveFinancials,
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
