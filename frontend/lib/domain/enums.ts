/**
 * Domain Enums - Ergonomic wrappers for generated OpenAPI enums.
 *
 * Some generated enums have awkward keys (e.g. `UserRole["Client_+_Financials"]`).
 * This module provides clean, uppercase constants that reference the generated values.
 *
 * Usage:
 *   import { USER_ROLE, HEALTH_STATUS } from "@/lib/domain/enums";
 *   if (user.role === USER_ROLE.CLIENT_FINANCIALS) { ... }
 */

import {
    UserRole,
    HealthStatus,
    ProjectType,
    ReportingCycle,
    ActionStatus,
    Priority,
    RiskStatus,
    RiskImpact,
    RiskProbability,
} from "@/lib/api/types";

// =============================================================================
// User Role Constants
// =============================================================================
export const USER_ROLE = {
    COGNITER: UserRole.Cogniter,
    CLIENT_FINANCIALS: UserRole["Client_+_Financials"],
    CLIENT: UserRole.Client,
} as const;

// =============================================================================
// Health Status Constants
// =============================================================================
export const HEALTH_STATUS = {
    GREEN: HealthStatus.Green,
    YELLOW: HealthStatus.Yellow,
    RED: HealthStatus.Red,
} as const;

// =============================================================================
// Project Type Constants
// =============================================================================
export const PROJECT_TYPE = {
    FIXED_PRICE: ProjectType.Fixed_Price,
    TIME_AND_MATERIALS: ProjectType["Time_&_Materials"],
    RETAINER: ProjectType.Retainer,
} as const;

// =============================================================================
// Reporting Cycle Constants
// =============================================================================
export const REPORTING_CYCLE = {
    WEEKLY: ReportingCycle.Weekly,
    BIWEEKLY: ReportingCycle["Bi-Weekly"],
    MONTHLY: ReportingCycle.Monthly,
} as const;

// =============================================================================
// Action Status Constants
// =============================================================================
export const ACTION_STATUS = {
    TO_DO: ActionStatus.To_Do,
    IN_PROGRESS: ActionStatus.In_Progress,
    COMPLETE: ActionStatus.Complete,
    NO_STATUS: ActionStatus.No_Status,
} as const;

// =============================================================================
// Priority Constants
// =============================================================================
export const PRIORITY = {
    HIGH: Priority.High,
    MEDIUM: Priority.Medium,
    LOW: Priority.Low,
} as const;

// =============================================================================
// Risk Status Constants
// =============================================================================
export const RISK_STATUS = {
    OPEN: RiskStatus.Open,
    CLOSED: RiskStatus.Closed,
    MITIGATED: RiskStatus.Mitigated,
} as const;

// =============================================================================
// Risk Impact Constants
// =============================================================================
export const RISK_IMPACT = {
    LOW: RiskImpact.Low,
    MEDIUM: RiskImpact.Medium,
    HIGH: RiskImpact.High,
} as const;

// =============================================================================
// Risk Probability Constants
// =============================================================================
export const RISK_PROBABILITY = {
    LOW: RiskProbability.Low,
    MEDIUM: RiskProbability.Medium,
    HIGH: RiskProbability.High,
} as const;
