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
import type { UserRole } from "@/lib/api/types";
import { USER_ROLE } from "@/lib/domain/enums";

/**
 * Check if user is an internal Cognite employee.
 * Internal users have full access to all features.
 */
export const isCogniter = (role: UserRole): boolean => {
    return role === USER_ROLE.COGNITER;
};

/**
 * Check if user can view financial data (budgets, burn rates, etc.).
 * Allowed for: COGNITER, CLIENT_FINANCIALS
 */
export const canViewFinancials = (role: UserRole): boolean => {
    return role === USER_ROLE.COGNITER || role === USER_ROLE.CLIENT_FINANCIALS;
};
