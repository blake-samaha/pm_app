"""Precursive/Salesforce integration package."""

from .field_mapper import map_salesforce_to_financials, map_salesforce_to_project
from .models import PrecursiveFinancials, PrecursiveProject, PrecursiveRisk
from .salesforce_schema import PrecursiveProjectFields

__all__ = [
    "PrecursiveProjectFields",
    "PrecursiveProject",
    "PrecursiveFinancials",
    "PrecursiveRisk",
    "map_salesforce_to_project",
    "map_salesforce_to_financials",
]
