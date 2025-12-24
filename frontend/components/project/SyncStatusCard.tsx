"use client";

import {
    RefreshCw,
    Database,
    CheckCircle,
    XCircle,
    Clock,
    Link as LinkIcon,
    Unlink,
    AlertTriangle,
} from "lucide-react";
import { SyncStatus, SyncJobSummary, SyncJobStatus } from "@/hooks/useSync";
import type { UserRole } from "@/lib/api/types";
import { USER_ROLE } from "@/lib/domain/enums";

interface SyncStatusCardProps {
    syncStatus: SyncStatus;
    userRole?: UserRole;
}

/**
 * Format a date string to a human-readable relative or absolute time.
 */
const formatTime = (dateString?: string): string => {
    if (!dateString) return "Never";

    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);

    if (diffMins < 1) return "Just now";
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffMins < 1440) return `${Math.floor(diffMins / 60)}h ago`;
    return date.toLocaleDateString();
};

/**
 * Get status badge color and icon.
 */
const getStatusDisplay = (status: SyncJobStatus) => {
    switch (status) {
        case "queued":
            return {
                color: "bg-yellow-100 text-yellow-800",
                icon: <Clock className="h-3 w-3" />,
                label: "Queued",
            };
        case "running":
            return {
                color: "bg-blue-100 text-blue-800",
                icon: <RefreshCw className="h-3 w-3 animate-spin" />,
                label: "Running",
            };
        case "succeeded":
            return {
                color: "bg-green-100 text-green-800",
                icon: <CheckCircle className="h-3 w-3" />,
                label: "Succeeded",
            };
        case "failed":
            return {
                color: "bg-red-100 text-red-800",
                icon: <XCircle className="h-3 w-3" />,
                label: "Failed",
            };
        default:
            return {
                color: "bg-slate-100 text-slate-800",
                icon: null,
                label: status,
            };
    }
};

/**
 * Job status row component.
 */
const JobStatusRow = ({
    label,
    icon,
    activeJob,
    lastJob,
    integrationConfigured,
    projectLinked,
    projectInfo,
    showErrors,
}: {
    label: string;
    icon: React.ReactNode;
    activeJob?: SyncJobSummary;
    lastJob?: SyncJobSummary;
    integrationConfigured: boolean;
    projectLinked: boolean;
    projectInfo?: string;
    showErrors: boolean;
}) => {
    const job = activeJob || lastJob;
    const statusDisplay = job ? getStatusDisplay(job.status) : null;

    return (
        <div className="space-y-1.5">
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                    {icon}
                    <span className="text-sm font-medium text-slate-700">{label}</span>
                </div>
                <div className="flex items-center gap-2">
                    {/* Integration configured status */}
                    {!integrationConfigured ? (
                        <span className="flex items-center gap-1 text-xs text-slate-400">
                            <AlertTriangle className="h-3 w-3" />
                            Not configured
                        </span>
                    ) : !projectLinked ? (
                        <span className="flex items-center gap-1 text-xs text-slate-400">
                            <Unlink className="h-3 w-3" />
                            Not linked
                        </span>
                    ) : (
                        <>
                            {/* Project info badge */}
                            {projectInfo && (
                                <span className="flex items-center gap-1 rounded bg-blue-100 px-2 py-0.5 text-xs font-medium text-blue-800">
                                    <LinkIcon className="h-3 w-3" />
                                    {projectInfo}
                                </span>
                            )}
                            {/* Job status badge */}
                            {statusDisplay && (
                                <span
                                    className={`flex items-center gap-1 rounded px-2 py-0.5 text-xs font-medium ${statusDisplay.color}`}
                                >
                                    {statusDisplay.icon}
                                    {statusDisplay.label}
                                </span>
                            )}
                        </>
                    )}
                </div>
            </div>

            {/* Job details row */}
            {job && integrationConfigured && projectLinked && (
                <div className="ml-6 flex items-center justify-between text-xs text-slate-500">
                    <span>
                        {job.items_synced > 0 ? `${job.items_synced} items` : "No items"}{" "}
                        {job.completed_at ? `• ${formatTime(job.completed_at)}` : ""}
                    </span>
                </div>
            )}

            {/* Error display (Cogniters only) */}
            {showErrors && job?.status === "failed" && job.error && (
                <div className="ml-6 mt-1 rounded bg-red-50 px-2 py-1 text-xs text-red-700">
                    {job.error}
                </div>
            )}
        </div>
    );
};

/**
 * Sync status card showing integration status, active jobs, and last job results.
 */
export const SyncStatusCard = ({ syncStatus, userRole }: SyncStatusCardProps) => {
    const isCogniter = userRole === USER_ROLE.COGNITER;
    const hasActiveJob = !!(syncStatus.jira_active_job || syncStatus.precursive_active_job);

    return (
        <div className="rounded-lg border border-slate-200 bg-white">
            <div className="border-b border-slate-100 px-4 py-3">
                <div className="flex items-center justify-between">
                    <h3 className="text-sm font-semibold text-slate-900">Sync Status</h3>
                    {hasActiveJob && (
                        <span className="flex items-center gap-1 text-xs text-blue-600">
                            <RefreshCw className="h-3 w-3 animate-spin" />
                            Syncing...
                        </span>
                    )}
                </div>
            </div>

            <div className="space-y-4 p-4">
                {/* Last synced */}
                <div className="flex items-center justify-between text-sm">
                    <span className="text-slate-500">Last synced</span>
                    <span className="font-medium text-slate-700">
                        {formatTime(syncStatus.last_synced_at)}
                    </span>
                </div>

                <div className="h-px bg-slate-100" />

                {/* Jira status */}
                <JobStatusRow
                    label="Jira"
                    icon={<RefreshCw className="h-4 w-4 text-slate-400" />}
                    activeJob={syncStatus.jira_active_job}
                    lastJob={syncStatus.jira_last_job}
                    integrationConfigured={syncStatus.jira_integration_configured}
                    projectLinked={syncStatus.jira_project_linked}
                    projectInfo={
                        syncStatus.jira_project_name
                            ? `${syncStatus.jira_project_name} (${syncStatus.jira_project_key})`
                            : syncStatus.jira_project_key
                    }
                    showErrors={isCogniter}
                />

                {/* Precursive status */}
                <JobStatusRow
                    label="Precursive"
                    icon={<Database className="h-4 w-4 text-slate-400" />}
                    activeJob={syncStatus.precursive_active_job}
                    lastJob={syncStatus.precursive_last_job}
                    integrationConfigured={syncStatus.precursive_integration_configured}
                    projectLinked={syncStatus.precursive_project_linked}
                    showErrors={isCogniter}
                />
            </div>
        </div>
    );
};

export default SyncStatusCard;
