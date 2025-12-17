"use client";

import { useParams } from "next/navigation";
import { useProject } from "@/hooks/useProjects";
import { useSyncStatus } from "@/hooks/useSync";
import { useAuthStore } from "@/store/authStore";
import { HealthIndicator } from "@/components/project/HealthIndicator";
import { FinancialsCard } from "@/components/project/FinancialsCard";
import { Timeline } from "@/components/project/Timeline";
import { ActionTable } from "@/components/project/ActionTable";
import { RiskList } from "@/components/project/RiskList";
import { SyncButton } from "@/components/project/SyncButton";
import { SprintGoalsCard } from "@/components/project/SprintGoalsCard";
import { ArrowLeft, Loader2, ExternalLink, Settings } from "lucide-react";
import Link from "next/link";
import ApiErrorDisplay from "@/components/ApiErrorDisplay";
import { getErrorMessage } from "@/lib/error";
import { useState } from "react";
import { EditProjectModal } from "@/components/project/EditProjectModal";
import { HealthStatus } from "@/types";

export default function ProjectDetailsPage() {
    const params = useParams();
    const { user } = useAuthStore();
    const projectId = params.id as string;
    const [isEditModalOpen, setIsEditModalOpen] = useState(false);

    const { data: project, isLoading, isError, error, refetch } = useProject(projectId);
    const {
        data: syncStatus,
        isLoading: statusLoading,
        isError: statusError,
        error: statusErrorObj,
        refetch: refetchStatus,
    } = useSyncStatus(projectId);

    // Auth check is now handled by AuthGuard

    if (isLoading) {
        return (
            <div className="flex min-h-screen items-center justify-center">
                <Loader2 className="h-8 w-8 animate-spin text-gray-400" />
            </div>
        );
    }

    if (isError || !project) {
        return (
            <div className="flex min-h-screen flex-col items-center justify-center px-6">
                <ApiErrorDisplay
                    title="Project failed to load"
                    error={getErrorMessage(error)}
                    onRetry={() => refetch()}
                />
                <Link href="/" className="mt-4 text-blue-600 hover:underline">
                    Back to Dashboard
                </Link>
            </div>
        );
    }

    const currentHealth = project.health_status_override || project.health_status;
    const isCritical = currentHealth === HealthStatus.RED || currentHealth === HealthStatus.YELLOW;

    // Dynamic header styling for critical states
    const headerBg = isCritical && currentHealth === HealthStatus.RED 
        ? "bg-red-50 border-b border-red-100" 
        : "bg-white";

    return (
        <div className="min-h-screen bg-gray-50 pb-12">
            {/* Header */}
            <header className={`${headerBg} shadow-sm transition-colors duration-300`}>
                <div className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
                    {/* Grid Layout: Left (Info), Center (Health), Right (Actions) */}
                    <div className="grid grid-cols-1 gap-4 md:grid-cols-3 items-center">
                        
                        {/* Left: Project Info */}
                        <div className="flex items-center space-x-4">
                            <Link
                                href="/"
                                className="text-gray-400 hover:text-gray-600"
                            >
                                <ArrowLeft className="h-6 w-6" />
                            </Link>
                            <div>
                                <h1 className="text-2xl font-bold text-gray-900 truncate">
                                    {project.name}
                                </h1>
                                <div className="mt-1 flex items-center space-x-4 text-sm text-gray-500">
                                    <a
                                        href={project.jira_url}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="flex items-center hover:text-blue-600"
                                    >
                                        Jira Board{" "}
                                        <ExternalLink className="ml-1 h-3 w-3" />
                                    </a>
                                    <span>•</span>
                                    <a
                                        href={project.precursive_url}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="flex items-center hover:text-blue-600"
                                    >
                                        Precursive{" "}
                                        <ExternalLink className="ml-1 h-3 w-3" />
                                    </a>
                                </div>
                            </div>
                        </div>

                        {/* Center: Hero Health Indicator */}
                        <div className="flex flex-col items-center justify-center">
                            <p className="mb-2 text-xs font-bold uppercase tracking-widest text-gray-400">
                                Overall Health
                            </p>
                            <HealthIndicator
                                status={currentHealth}
                                label={currentHealth}
                                size="xl"
                                variant="solid"
                            />
                        </div>

                        {/* Right: Actions */}
                        <div className="flex items-center justify-end space-x-6">
                            {user?.role === "Cogniter" && (
                                <>
                                    <button
                                        onClick={() => setIsEditModalOpen(true)}
                                        className="rounded-md p-2 text-gray-400 hover:bg-gray-100 hover:text-gray-600"
                                        title="Project Settings"
                                    >
                                        <Settings className="h-5 w-5" />
                                    </button>
                                    <SyncButton projectId={project.id} />
                                </>
                            )}
                        </div>
                    </div>
                </div>
            </header>

            <main className="mx-auto mt-8 max-w-7xl px-4 sm:px-6 lg:px-8">
                <div className="grid gap-8 lg:grid-cols-3">
                    {/* Left Column (2/3 width) */}
                    <div className="space-y-8 lg:col-span-2">
                        <Timeline project={project} />
                        <SprintGoalsCard
                            sprintGoals={project.sprint_goals}
                            projectId={project.id}
                            canEdit={user?.role === "Cogniter"}
                        />
                        <ActionTable projectId={project.id} />
                    </div>

                    {/* Right Column (1/3 width) */}
                    <div className="space-y-8">
                        <div>
                            {statusLoading && (
                                <div className="flex items-center justify-center rounded-lg border border-gray-200 bg-white p-4">
                                    <Loader2 className="h-5 w-5 animate-spin text-gray-400" />
                                </div>
                            )}
                            {statusError && (
                                <ApiErrorDisplay
                                    title="Sync status unavailable"
                                    error={getErrorMessage(statusErrorObj)}
                                    onRetry={() => refetchStatus()}
                                />
                            )}
                            {!statusLoading && !statusError && syncStatus && (
                                <div className="rounded-lg border border-gray-200 bg-white p-4 space-y-2">
                                    <div className="flex items-center justify-between">
                                        <span className="text-sm font-medium text-gray-700">Last synced</span>
                                        <span className="text-sm text-gray-600">
                                            {syncStatus.last_synced_at
                                                ? new Date(syncStatus.last_synced_at).toLocaleString()
                                                : "Never"}
                                        </span>
                                    </div>
                                    <div className="flex items-center justify-between">
                                        <span className="text-sm font-medium text-gray-700">Jira configured</span>
                                        <div className="flex items-center space-x-2">
                                            {syncStatus.jira_project_key && (
                                                <span 
                                                    className="rounded bg-blue-100 px-2 py-0.5 text-xs font-medium text-blue-800"
                                                    title={syncStatus.jira_project_name || syncStatus.jira_project_key}
                                                >
                                                    {syncStatus.jira_project_name ? (
                                                        <>
                                                            {syncStatus.jira_project_name} 
                                                            <span className="opacity-75 ml-1">({syncStatus.jira_project_key})</span>
                                                        </>
                                                    ) : (
                                                        syncStatus.jira_project_key
                                                    )}
                                                </span>
                                            )}
                                            <span className="text-sm text-gray-600">
                                                {syncStatus.jira_configured ? "Yes" : "No"}
                                            </span>
                                        </div>
                                    </div>
                                    <div className="flex items-center justify-between">
                                        <span className="text-sm font-medium text-gray-700">Precursive configured</span>
                                        <span className="text-sm text-gray-600">
                                            {syncStatus.precursive_configured ? "Yes" : "No"}
                                        </span>
                                    </div>
                                    <div className="flex items-center justify-between">
                                        <span className="text-sm font-medium text-gray-700">Precursive last success</span>
                                        <span className="text-sm text-gray-600">
                                            {syncStatus.last_precursive_sync_success === undefined
                                                ? "Unknown"
                                                : syncStatus.last_precursive_sync_success
                                                    ? "Yes"
                                                    : "No"}
                                        </span>
                                    </div>
                                </div>
                            )}
                        </div>
                        <FinancialsCard project={project} />
                        <RiskList projectId={project.id} />
                    </div>
                </div>
            </main>

            <EditProjectModal 
                project={project}
                isOpen={isEditModalOpen}
                onClose={() => setIsEditModalOpen(false)}
            />
        </div>
    );
}
