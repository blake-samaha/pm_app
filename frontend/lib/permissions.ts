/**
 * Centralized permission logic for role-based access control.
 *
 * This module provides simple, reusable permission checks for the frontend.
 * All functions take a UserRole and return a boolean.
 *
 * Role Hierarchy:
 * - COGNITER: Internal Cognite employees - full access
 * - CLIENT_FINANCIALS: Senior client stakeholders - can view financials
 * - CLIENT: Standard client stakeholders - basic access only
 */
import { UserRole } from "@/types";

/**
 * Check if user is an internal Cognite employee.
 * Internal users have full access to all features.
 */
export const isCogniter = (role: UserRole): boolean => {
    return role === UserRole.COGNITER;
};

/**
 * Check if user has any client-type role.
 * Client roles require explicit project assignment.
 */
export const isClientRole = (role: UserRole): boolean => {
    return role === UserRole.CLIENT || role === UserRole.CLIENT_FINANCIALS;
};

/**
 * Check if user can view financial data (budgets, burn rates, etc.).
 * Allowed for: COGNITER, CLIENT_FINANCIALS
 */
export const canViewFinancials = (role: UserRole): boolean => {
    return role === UserRole.COGNITER || role === UserRole.CLIENT_FINANCIALS;
};

/**
 * Check if user can manage team assignments on projects.
 * Only internal users (Cogniters) can manage teams.
 */
export const canManageTeam = (role: UserRole): boolean => {
    return role === UserRole.COGNITER;
};

/**
 * Check if user can edit project settings and metadata.
 * Only internal users (Cogniters) can edit projects.
 */
export const canEditProject = (role: UserRole): boolean => {
    return role === UserRole.COGNITER;
};

/**
 * Check if user can create new projects.
 * Only internal users (Cogniters) can create projects.
 */
export const canCreateProject = (role: UserRole): boolean => {
    return role === UserRole.COGNITER;
};
