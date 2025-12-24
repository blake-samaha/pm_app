/**
 * API Types - Stable import surface for generated OpenAPI models.
 *
 * This barrel re-exports commonly used generated models/enums so consumers
 * do not couple to the Orval file layout. Import from here instead of
 * directly from `lib/api/generated/models/*`.
 *
 * These types are contract-driven: they are generated from the backend
 * OpenAPI schema via `make api-generate`. Do not define manual types here.
 */

// Import types for aliasing
import type {
    ProjectRead as ProjectReadType,
    ActionItemRead as ActionItemReadType,
    RiskRead as RiskReadType,
    CommentRead as CommentReadType,
    UserRead as UserReadType,
} from "./generated/models";

// =============================================================================
// Project Types
// =============================================================================
export type { ProjectRead, ProjectCreate, ProjectUpdate } from "./generated/models";

export { ProjectType, ReportingCycle, HealthStatus } from "./generated/models";

// =============================================================================
// Action Item Types
// =============================================================================
export type { ActionItemRead, ActionItemCreate } from "./generated/models";

export { ActionStatus, Priority } from "./generated/models";

// =============================================================================
// Risk Types
// =============================================================================
export type { RiskRead, RiskCreate, RiskResolve, RiskReopen } from "./generated/models";

export { RiskStatus, RiskImpact, RiskProbability } from "./generated/models";

// =============================================================================
// Comment Types
// =============================================================================
export type { CommentRead, CommentCreate } from "./generated/models";

// =============================================================================
// User Types
// =============================================================================
export type {
    UserRead,
    InviteUserRequest,
    InviteUserResponse,
    UserRoleUpdate,
} from "./generated/models";

export { UserRole } from "./generated/models";

// =============================================================================
// Sync Types
// =============================================================================
export type {
    SyncStatus,
    SyncResult,
    SyncJobRead,
    SyncJobSummary,
    SyncJobEnqueued,
} from "./generated/models";

export { SyncJobStatus, SyncJobType } from "./generated/models";

// =============================================================================
// Convenience Type Aliases
// =============================================================================

/**
 * Alias for UserRead - represents a user in the system.
 * This provides semantic clarity when used in contexts like authStore.
 */
export type User = UserReadType;

/**
 * Alias for ProjectRead - represents a project in the system.
 */
export type Project = ProjectReadType;

/**
 * Alias for ActionItemRead - represents an action item in the system.
 */
export type ActionItem = ActionItemReadType;

/**
 * Alias for RiskRead - represents a risk in the system.
 */
export type Risk = RiskReadType;

/**
 * Alias for CommentRead - represents a comment in the system.
 */
export type Comment = CommentReadType;
