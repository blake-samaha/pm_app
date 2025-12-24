import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { useAuthStore } from "@/store/authStore";

// ============================================================================
// Types matching backend schemas
// ============================================================================

export type SyncJobStatus = "queued" | "running" | "succeeded" | "failed";
export type SyncJobType = "jira" | "precursive" | "full";

export interface SyncJobSummary {
    id: string;
    job_type: SyncJobType;
    status: SyncJobStatus;
    created_at: string;
    started_at?: string;
    completed_at?: string;
    items_synced: number;
    error?: string;
}

export interface SyncStatus {
    project_id: string;
    last_synced_at?: string;

    // Integration configured (from backend settings/credentials)
    jira_integration_configured: boolean;
    precursive_integration_configured: boolean;

    // Project linked (project has URL/key/ID)
    jira_project_linked: boolean;
    precursive_project_linked: boolean;

    // Project-level info (for display)
    jira_project_key?: string;
    jira_project_name?: string;

    // Active jobs (queued or running)
    jira_active_job?: SyncJobSummary;
    precursive_active_job?: SyncJobSummary;

    // Last completed jobs (succeeded or failed)
    jira_last_job?: SyncJobSummary;
    precursive_last_job?: SyncJobSummary;
}

export interface SyncJobEnqueued {
    job_id: string;
    status: SyncJobStatus;
    message: string;
    accepted: boolean;
    deduplicated: boolean;
}

// ============================================================================
// Hooks
// ============================================================================

/**
 * Fetch sync status for a project.
 *
 * When there's an active job (queued/running), polls every 1.5s.
 * Otherwise, no polling.
 */
export const useSyncStatus = (projectId: string) => {
    const { isAuthenticated } = useAuthStore();

    return useQuery<SyncStatus>({
        queryKey: ["sync-status", projectId],
        queryFn: async () => {
            const response = await api.get(`/sync/${projectId}/status`);
            return response.data;
        },
        enabled: !!projectId && isAuthenticated,
        refetchInterval: (query) => {
            const data = query.state.data;
            // Poll while there's an active job
            if (data?.jira_active_job || data?.precursive_active_job) {
                return 1500; // 1.5 seconds
            }
            return false; // No polling
        },
    });
};

/**
 * Trigger a Jira sync for a project.
 */
export const useTriggerJiraSync = () => {
    const queryClient = useQueryClient();

    return useMutation<SyncJobEnqueued, Error, string>({
        mutationFn: async (projectId: string) => {
            const response = await api.post(`/sync/${projectId}/jira`);
            return response.data;
        },
        onSuccess: (data, projectId) => {
            // Immediately invalidate sync status to show active job
            queryClient.invalidateQueries({ queryKey: ["sync-status", projectId] });
        },
    });
};

/**
 * Trigger a Precursive sync for a project.
 */
export const useTriggerPrecursiveSync = () => {
    const queryClient = useQueryClient();

    return useMutation<SyncJobEnqueued, Error, string>({
        mutationFn: async (projectId: string) => {
            const response = await api.post(`/sync/${projectId}/precursive`);
            return response.data;
        },
        onSuccess: (data, projectId) => {
            // Immediately invalidate sync status to show active job
            queryClient.invalidateQueries({ queryKey: ["sync-status", projectId] });
        },
    });
};

/**
 * Helper to check if any sync job is active for a project.
 */
export const hasActiveJob = (status: SyncStatus | undefined): boolean => {
    return !!(status?.jira_active_job || status?.precursive_active_job);
};

/**
 * Helper to check if a specific job type is active.
 */
export const isJobActive = (
    status: SyncStatus | undefined,
    type: "jira" | "precursive"
): boolean => {
    if (!status) return false;
    if (type === "jira") return !!status.jira_active_job;
    return !!status.precursive_active_job;
};
