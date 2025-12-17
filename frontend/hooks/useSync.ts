import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { useAuthStore } from "@/store/authStore";

export interface SyncStatus {
    project_id: string;
    last_synced_at?: string;
    jira_configured: boolean;
    precursive_configured: boolean;
    last_jira_items_count?: number;
    last_precursive_sync_success?: boolean;
    jira_project_key?: string;
    jira_project_name?: string;
}

export const useSyncStatus = (projectId: string) => {
    const { isAuthenticated } = useAuthStore();
    return useQuery<SyncStatus>({
        queryKey: ["sync-status", projectId],
        queryFn: async () => {
            const response = await api.get(`/sync/${projectId}/status`);
            return response.data;
        },
        enabled: !!projectId && isAuthenticated,
    });
};
