"use client";

import { useEffect, useRef } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { getErrorMessage, getErrorStatus } from "@/lib/error";
import { RefreshCw, Database, AlertTriangle, CheckCircle, XCircle } from "lucide-react";
import { toast } from "sonner";
import {
    useSyncStatus,
    useTriggerJiraSync,
    useTriggerPrecursiveSync,
    SyncJobSummary,
} from "@/hooks/useSync";

interface SyncButtonProps {
    projectId: string;
}

/**
 * Jira sync button - handles async job pattern with proper status polling.
 */
export const JiraSyncButton = ({ projectId }: SyncButtonProps) => {
    const queryClient = useQueryClient();
    const { data: syncStatus } = useSyncStatus(projectId);
    const triggerSync = useTriggerJiraSync();

    // Track the last job we've shown a completion toast for
    const lastToastedJobRef = useRef<string | null>(null);

    const isActive = !!syncStatus?.jira_active_job;
    const lastJob = syncStatus?.jira_last_job;

    // Effect to handle job completion: show toast + invalidate queries
    useEffect(() => {
        if (!lastJob) return;

        // Only show toast if this is a "new" completion we haven't toasted yet
        if (lastToastedJobRef.current === lastJob.id) return;

        // Check if job just completed (status is terminal)
        if (lastJob.status === "succeeded" || lastJob.status === "failed") {
            lastToastedJobRef.current = lastJob.id;

            if (lastJob.status === "succeeded") {
                toast.success("Jira sync completed", {
                    description: `Synced ${lastJob.items_synced} items`,
                    icon: <CheckCircle className="h-4 w-4 text-green-500" />,
                });

                // Invalidate queries to refresh data
                queryClient.invalidateQueries({ queryKey: ["actions", projectId] });
                queryClient.invalidateQueries({ queryKey: ["projects", projectId] });
            } else if (lastJob.status === "failed") {
                toast.error("Jira sync failed", {
                    description: lastJob.error || "An error occurred during sync",
                    icon: <XCircle className="h-4 w-4 text-red-500" />,
                });
            }
        }
    }, [lastJob, projectId, queryClient]);

    const handleSync = async () => {
        try {
            const result = await triggerSync.mutateAsync(projectId);

            if (result.deduplicated) {
                toast.info("Jira sync in progress", {
                    description: "A sync is already running for this project.",
                });
            } else {
                toast.success("Jira sync started", {
                    description: result.message,
                });
            }
        } catch (err) {
            console.error("Jira sync failed", err);
            toast.error("Jira sync failed", {
                description: getErrorMessage(err),
            });
        }
    };

    return (
        <button
            onClick={handleSync}
            disabled={isActive || triggerSync.isPending}
            className="flex items-center rounded-md bg-white px-3 py-2 text-sm font-medium text-gray-700 shadow-sm hover:bg-gray-50 disabled:opacity-50"
        >
            <RefreshCw className={`mr-2 h-4 w-4 ${isActive ? "animate-spin" : ""}`} />
            {isActive ? "Syncing..." : "Sync Jira"}
        </button>
    );
};

/**
 * Precursive sync button - handles async job pattern with proper status polling.
 */
export const PrecursiveSyncButton = ({ projectId }: SyncButtonProps) => {
    const queryClient = useQueryClient();
    const { data: syncStatus } = useSyncStatus(projectId);
    const triggerSync = useTriggerPrecursiveSync();

    // Track the last job we've shown a completion toast for
    const lastToastedJobRef = useRef<string | null>(null);

    const isActive = !!syncStatus?.precursive_active_job;
    const lastJob = syncStatus?.precursive_last_job;

    // Effect to handle job completion: show toast + invalidate queries
    useEffect(() => {
        if (!lastJob) return;

        // Only show toast if this is a "new" completion we haven't toasted yet
        if (lastToastedJobRef.current === lastJob.id) return;

        // Check if job just completed (status is terminal)
        if (lastJob.status === "succeeded" || lastJob.status === "failed") {
            lastToastedJobRef.current = lastJob.id;

            if (lastJob.status === "succeeded") {
                toast.success("Precursive sync completed", {
                    description: `Synced ${lastJob.items_synced} items`,
                    icon: <CheckCircle className="h-4 w-4 text-green-500" />,
                });

                // Invalidate queries to refresh data
                queryClient.invalidateQueries({ queryKey: ["risks", projectId] });
                queryClient.invalidateQueries({ queryKey: ["projects", projectId] });
            } else if (lastJob.status === "failed") {
                toast.error("Precursive sync failed", {
                    description: lastJob.error || "An error occurred during sync",
                    icon: <XCircle className="h-4 w-4 text-red-500" />,
                });
            }
        }
    }, [lastJob, projectId, queryClient]);

    const handleSync = async () => {
        try {
            const result = await triggerSync.mutateAsync(projectId);

            if (result.deduplicated) {
                toast.info("Precursive sync in progress", {
                    description: "A sync is already running for this project.",
                });
            } else {
                toast.success("Precursive sync started", {
                    description: result.message,
                });
            }
        } catch (err) {
            console.error("Precursive sync failed", err);
            const status = getErrorStatus(err);

            if (status === 503) {
                toast.error("Precursive unavailable", {
                    description:
                        "Precursive integration is not configured or Salesforce is unavailable.",
                    icon: <AlertTriangle className="h-4 w-4" />,
                });
            } else {
                toast.error("Precursive sync failed", {
                    description: getErrorMessage(err),
                });
            }
        }
    };

    return (
        <button
            onClick={handleSync}
            disabled={isActive || triggerSync.isPending}
            className="flex items-center rounded-md bg-blue-50 px-3 py-2 text-sm font-medium text-blue-700 shadow-sm hover:bg-blue-100 disabled:opacity-50"
            title="Sync from Precursive/Salesforce (use sparingly - limited API calls)"
        >
            <Database className={`mr-2 h-4 w-4 ${isActive ? "animate-pulse" : ""}`} />
            {isActive ? "Syncing..." : "Sync Precursive"}
        </button>
    );
};

/**
 * Combined sync buttons component - renders both Jira and Precursive buttons.
 */
export const SyncButtons = ({ projectId }: SyncButtonProps) => {
    return (
        <div className="flex items-center gap-2">
            <JiraSyncButton projectId={projectId} />
            <PrecursiveSyncButton projectId={projectId} />
        </div>
    );
};

/**
 * @deprecated Use JiraSyncButton, PrecursiveSyncButton, or SyncButtons instead.
 */
export const SyncButton = JiraSyncButton;
