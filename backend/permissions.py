"""
Centralized permission logic using pure functions.

This module provides simple, testable permission checks for role-based access control.
All functions are pure (no side effects) and take a User object as input.

Role Hierarchy:
- COGNITER: Internal Cognite employees - full access to everything
- CLIENT_FINANCIALS: Senior client stakeholders - can view financials
- CLIENT: Standard client stakeholders - basic access only

All client roles (CLIENT, CLIENT_FINANCIALS) require explicit project assignment
to access project data. This is enforced at the router/service level, not here.

Note on Redundancy:
Several functions below (can_manage_team, can_edit_project, can_create_project,
can_resolve_risk, can_reopen_risk, can_delete_action, can_update_risk, can_delete_risk,
can_publish_project) have identical implementations: `return user.role == UserRole.COGNITER`.

This is intentional for:
1. Semantic clarity - each function documents a specific capability
2. Future flexibility - permissions can evolve independently without refactoring callers
3. Explicit access control - callers import the specific permission they need
"""

from models import User, UserRole


def is_internal_user(user: User) -> bool:
    """
    Check if user is an internal Cognite employee.

    Internal users have full access to all features and all projects.
    """
    return user.role == UserRole.COGNITER


def can_view_financials(user: User) -> bool:
    """
    Check if user can view financial data (budgets, burn rates, etc.).

    Allowed for: COGNITER, CLIENT_FINANCIALS
    Denied for: CLIENT
    """
    return user.role in (UserRole.COGNITER, UserRole.CLIENT_FINANCIALS)


def can_manage_team(user: User) -> bool:
    """
    Check if user can manage team assignments on projects.

    This includes assigning/removing users and sending invitations.
    Only internal users (Cogniters) can manage teams.
    """
    return user.role == UserRole.COGNITER


def can_edit_project(user: User) -> bool:
    """
    Check if user can edit project settings and metadata.

    This includes changing project name, URLs, health status, etc.
    Only internal users (Cogniters) can edit projects.
    """
    return user.role == UserRole.COGNITER


def can_create_project(user: User) -> bool:
    """
    Check if user can create new projects.

    Only internal users (Cogniters) can create projects.
    """
    return user.role == UserRole.COGNITER


def can_resolve_risk(user: User) -> bool:
    """
    Check if user can resolve (close/mitigate) risks.

    Only internal users (Cogniters) can change risk status.
    Clients can comment on risks but not resolve them.
    """
    return user.role == UserRole.COGNITER


def can_reopen_risk(user: User) -> bool:
    """
    Check if user can reopen a resolved risk.

    Only internal users (Cogniters) can reopen risks.
    """
    return user.role == UserRole.COGNITER


def can_delete_action(user: User) -> bool:
    """
    Check if user can delete action items.

    Only internal users (Cogniters) can delete action items.
    """
    return user.role == UserRole.COGNITER


def can_update_risk(user: User) -> bool:
    """
    Check if user can update risk details (not status changes).

    Only internal users (Cogniters) can update risks.
    """
    return user.role == UserRole.COGNITER


def can_delete_risk(user: User) -> bool:
    """
    Check if user can delete risks.

    Only internal users (Cogniters) can delete risks.
    """
    return user.role == UserRole.COGNITER


def can_publish_project(user: User) -> bool:
    """
    Check if user can publish or unpublish projects.

    Only internal users (Cogniters) can publish/unpublish projects.
    """
    return user.role == UserRole.COGNITER
