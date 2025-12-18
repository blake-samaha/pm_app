"use client";

import { useParams } from "next/navigation";
import { useProject } from "@/hooks/useProjects";
import { useSyncStatus } from "@/hooks/useSync";
import { useEffectiveUser } from "@/hooks/useEffectiveUser";
import { HealthIndicator } from "@/components/project/HealthIndicator";
import { FinancialsCard } from "@/components/project/FinancialsCard";
import { Timeline } from "@/components/project/Timeline";
import { ActionTable } from "@/components/project/ActionTable";
import { RiskList } from "@/components/project/RiskList";
import { RiskMatrix } from "@/components/project/RiskMatrix"; // Imported RiskMatrix
import { useRisks } from "@/hooks/useRisks"; // Import useRisks to pass data to Matrix
import { RiskImpact, RiskProbability } from "@/types/actions-risks";
import { SyncButton } from "@/components/project/SyncButton";
import { SprintGoalsCard } from "@/components/project/SprintGoalsCard";
import { TeamSection } from "@/components/project/TeamSection";
import {
    ArrowLeft,
    Loader2,
    ExternalLink,
    Settings,
    CheckSquare,
    DollarSign,
    Users,
    ShieldAlert,
    X,
} from "lucide-react";
import Link from "next/link";
import ApiErrorDisplay from "@/components/ApiErrorDisplay";
import { getErrorMessage } from "@/lib/error";
import { API_URL } from "@/lib/api";
import { useState } from "react";
import { EditProjectModal } from "@/components/project/EditProjectModal";
import { HealthStatus, UserRole } from "@/types";
import { canViewFinancials } from "@/lib/permissions";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { Skeleton } from "@/components/ui/skeleton";

/**
 * Get the full URL for a logo, handling both local uploads and external URLs.
 */
const getLogoUrl = (url: string | undefined | null): string | null => {
    if (!url) return null;
    if (url.startsWith("/uploads/")) {
        return `${API_URL}${url}`;
    }
    return url;
};

export default function ProjectDetailsPage() {
    const params = useParams();
    const user = useEffectiveUser();
    const projectId = params.id as string;
    const [isEditModalOpen, setIsEditModalOpen] = useState(false);
    const [logoError, setLogoError] = useState(false);
    const [activeTab, setActiveTab] = useState("work");
    const isCogniterUser = !!user && user.role === UserRole.COGNITER;
    const canSeeFinancials = !!user && canViewFinancials(user.role);

    const { data: project, isLoading, isError, error, refetch } = useProject(projectId);
    const { data: risks } = useRisks(projectId); // Fetch risks here for the Matrix
    const [matrixFilter, setMatrixFilter] = useState<{
        probability: RiskProbability;
        impact: RiskImpact;
    } | null>(null);
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
            <div className="min-h-screen bg-slate-50 pb-12">
                <div className="border-b border-slate-200 bg-white shadow-sm">
                    <div className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
                        <div className="flex flex-col gap-6">
                            <div className="flex items-center space-x-4">
                                <Skeleton className="h-12 w-12 rounded-lg" />
                                <div className="space-y-2">
                                    <Skeleton className="h-8 w-64" />
                                    <Skeleton className="h-4 w-48" />
                                </div>
                            </div>
                            <div className="flex space-x-6">
                                <Skeleton className="h-8 w-32" />
                                <Skeleton className="h-8 w-32" />
                                <Skeleton className="h-8 w-32" />
                            </div>
                        </div>
                    </div>
                </div>
                <main className="mx-auto mt-8 max-w-7xl px-4 sm:px-6 lg:px-8">
                    <div className="grid gap-8 lg:grid-cols-3">
                        <div className="space-y-8 lg:col-span-2">
                            <Skeleton className="h-48 w-full rounded-xl" />
                            <Skeleton className="h-96 w-full rounded-xl" />
                        </div>
                        <div className="space-y-8">
                            <Skeleton className="h-64 w-full rounded-xl" />
                            <Skeleton className="h-64 w-full rounded-xl" />
                        </div>
                    </div>
                </main>
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

    // Define styles based on health status
    const healthStyles = {
        [HealthStatus.GREEN]: {
            border: "border-green-500",
            bg: "bg-green-50",
            text: "text-green-700",
            shadow: "shadow-green-100",
        },
        [HealthStatus.YELLOW]: {
            border: "border-yellow-500",
            bg: "bg-yellow-50",
            text: "text-yellow-700",
            shadow: "shadow-yellow-100",
        },
        [HealthStatus.RED]: {
            border: "border-red-500",
            bg: "bg-red-50",
            text: "text-red-700",
            shadow: "shadow-red-100",
        },
    };

    const currentStyle = healthStyles[currentHealth] || healthStyles[HealthStatus.GREEN];

    return (
        <div className="min-h-screen bg-slate-50 pb-12">
            {/* Header with Health Status Indicator */}
            <header
                className={`relative shadow-sm transition-all duration-300 ${currentStyle.bg} border-b border-slate-200`}
            >
                {/* Top Health Border Strip */}
                <div className={`absolute left-0 right-0 top-0 h-1.5 ${currentStyle.border}`} />

                <div className="mx-auto max-w-screen-2xl px-4 py-4 pt-6 sm:px-6 lg:px-8">
                    {/* Top Row: Navigation & Actions */}
                    <div className="mb-6 flex flex-col justify-between gap-4 md:flex-row md:items-center">
                        {/* Left: Project Info */}
                        <div className="flex items-center space-x-4">
                            <Link href="/" className="text-slate-400 hover:text-slate-600">
                                <ArrowLeft className="h-6 w-6" />
                            </Link>
                            {/* Project Logo */}
                            {(() => {
                                const logoUrl = getLogoUrl(project.client_logo_url);
                                const showLogo = logoUrl && !logoError;
                                return showLogo ? (
                                    <img
                                        src={logoUrl}
                                        alt={`${project.name} logo`}
                                        className="h-12 w-12 rounded-lg bg-slate-50 object-cover shadow-sm ring-1 ring-slate-900/5"
                                        onError={() => setLogoError(true)}
                                    />
                                ) : (
                                    <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-gradient-to-br from-slate-100 to-slate-200 text-xl font-bold text-slate-500 shadow-sm ring-1 ring-slate-900/5">
                                        {project.name.charAt(0).toUpperCase()}
                                    </div>
                                );
                            })()}
                            <div>
                                <h1 className="truncate text-2xl font-bold text-slate-900">
                                    {project.name}
                                </h1>
                                <div className="mt-1 flex items-center space-x-4 text-sm text-slate-500">
                                    <a
                                        href={project.jira_url}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="flex items-center transition-colors hover:text-blue-600"
                                    >
                                        Jira Board <ExternalLink className="ml-1 h-3 w-3" />
                                    </a>
                                    <span className="text-slate-300">•</span>
                                    <a
                                        href={project.precursive_url}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="flex items-center transition-colors hover:text-blue-600"
                                    >
                                        Precursive <ExternalLink className="ml-1 h-3 w-3" />
                                    </a>
                                </div>
                            </div>
                        </div>

                        {/* Right: Actions */}
                        <div className="flex items-center space-x-4">
                            {/* Enhanced Health Status Display */}
                            <div
                                className={`mr-4 flex items-center rounded-lg border bg-white px-3 py-1.5 shadow-sm ${currentStyle.shadow} border-slate-100`}
                            >
                                <p className="mr-3 text-xs font-bold uppercase tracking-widest text-slate-400">
                                    Health
                                </p>
                                <HealthIndicator
                                    status={currentHealth}
                                    label={currentHealth}
                                    size="md"
                                    variant="solid"
                                />
                            </div>

                            {user?.role === "Cogniter" && (
                                <>
                                    <SyncButton projectId={project.id} />
                                    <button
                                        onClick={() => setIsEditModalOpen(true)}
                                        className="rounded-md p-2 text-slate-400 transition-colors hover:bg-slate-100 hover:text-slate-600"
                                        title="Project Settings"
                                    >
                                        <Settings className="h-5 w-5" />
                                    </button>
                                </>
                            )}
                        </div>
                    </div>

                    {/* Bottom Row: Tabs */}
                    <div className="mt-2 overflow-x-auto pb-1">
                        <TabsList className="min-w-max space-x-6 bg-transparent p-0">
                            <TabsTrigger
                                isActive={activeTab === "work"}
                                onClick={() => setActiveTab("work")}
                                className="rounded-none border-b-2 border-transparent bg-transparent p-0 pb-2 text-base shadow-none data-[state=active]:border-indigo-600"
                            >
                                <div className="flex items-center space-x-2">
                                    <CheckSquare
                                        className={`h-4 w-4 ${activeTab === "work" ? "text-indigo-600" : ""}`}
                                    />
                                    <span className={activeTab === "work" ? "text-indigo-600" : ""}>
                                        Work & Sprints
                                    </span>
                                </div>
                            </TabsTrigger>
                            <TabsTrigger
                                isActive={activeTab === "risks"}
                                onClick={() => setActiveTab("risks")}
                                className="rounded-none border-b-2 border-transparent bg-transparent p-0 pb-2 text-base shadow-none data-[state=active]:border-indigo-600"
                            >
                                <div className="flex items-center space-x-2">
                                    <ShieldAlert
                                        className={`h-4 w-4 ${activeTab === "risks" ? "text-indigo-600" : ""}`}
                                    />
                                    <span
                                        className={activeTab === "risks" ? "text-indigo-600" : ""}
                                    >
                                        Risks
                                    </span>
                                </div>
                            </TabsTrigger>
                            {canSeeFinancials && (
                                <TabsTrigger
                                    isActive={activeTab === "financials"}
                                    onClick={() => setActiveTab("financials")}
                                    className="rounded-none border-b-2 border-transparent bg-transparent p-0 pb-2 text-base shadow-none data-[state=active]:border-indigo-600"
                                >
                                    <div className="flex items-center space-x-2">
                                        <DollarSign
                                            className={`h-4 w-4 ${activeTab === "financials" ? "text-indigo-600" : ""}`}
                                        />
                                        <span
                                            className={
                                                activeTab === "financials" ? "text-indigo-600" : ""
                                            }
                                        >
                                            Financials
                                        </span>
                                    </div>
                                </TabsTrigger>
                            )}
                            {isCogniterUser && (
                                <TabsTrigger
                                    isActive={activeTab === "team"}
                                    onClick={() => setActiveTab("team")}
                                    className="rounded-none border-b-2 border-transparent bg-transparent p-0 pb-2 text-base shadow-none data-[state=active]:border-indigo-600"
                                >
                                    <div className="flex items-center space-x-2">
                                        <Users
                                            className={`h-4 w-4 ${activeTab === "team" ? "text-indigo-600" : ""}`}
                                        />
                                        <span
                                            className={
                                                activeTab === "team" ? "text-indigo-600" : ""
                                            }
                                        >
                                            Team
                                        </span>
                                    </div>
                                </TabsTrigger>
                            )}
                        </TabsList>
                    </div>
                </div>
            </header>

            <main className="mx-auto mt-6 max-w-screen-2xl px-4 sm:px-6 lg:px-8">
                {/* Work & Sprints View */}
                <TabsContent isActive={activeTab === "work"}>
                    <div className="grid gap-6 lg:grid-cols-12">
                        {/* Left Column (Main Content) */}
                        <div className="space-y-6 lg:col-span-8 xl:col-span-9">
                            <SprintGoalsCard
                                sprintGoals={project.sprint_goals}
                                projectId={project.id}
                                canEdit={user?.role === "Cogniter"}
                            />
                            <ActionTable projectId={project.id} />
                        </div>

                        {/* Right Column (Sidebar) */}
                        <div className="space-y-6 lg:col-span-4 xl:col-span-3">
                            <Timeline project={project} />

                            {/* Sync Status Card */}
                            <div>
                                {statusLoading && (
                                    <div className="flex items-center justify-center rounded-lg border border-slate-200 bg-white p-4">
                                        <Loader2 className="h-5 w-5 animate-spin text-slate-400" />
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
                                    <div className="space-y-2 rounded-lg border border-slate-200 bg-white p-4">
                                        <div className="flex items-center justify-between">
                                            <span className="text-sm font-medium text-slate-700">
                                                Last synced
                                            </span>
                                            <span className="text-sm text-slate-600">
                                                {syncStatus.last_synced_at
                                                    ? new Date(
                                                          syncStatus.last_synced_at
                                                      ).toLocaleString()
                                                    : "Never"}
                                            </span>
                                        </div>
                                        <div className="flex items-center justify-between">
                                            <span className="text-sm font-medium text-slate-700">
                                                Jira configured
                                            </span>
                                            <div className="flex items-center space-x-2">
                                                {syncStatus.jira_project_key && (
                                                    <span
                                                        className="rounded bg-blue-100 px-2 py-0.5 text-xs font-medium text-blue-800"
                                                        title={
                                                            syncStatus.jira_project_name ||
                                                            syncStatus.jira_project_key
                                                        }
                                                    >
                                                        {syncStatus.jira_project_name ? (
                                                            <>
                                                                {syncStatus.jira_project_name}
                                                                <span className="ml-1 opacity-75">
                                                                    ({syncStatus.jira_project_key})
                                                                </span>
                                                            </>
                                                        ) : (
                                                            syncStatus.jira_project_key
                                                        )}
                                                    </span>
                                                )}
                                                <span className="text-sm text-slate-600">
                                                    {syncStatus.jira_configured ? "Yes" : "No"}
                                                </span>
                                            </div>
                                        </div>
                                    </div>
                                )}
                            </div>

                            {/* Removed sidebar RiskList */}
                        </div>
                    </div>
                </TabsContent>

                {/* Risks View - NEW TAB */}
                <TabsContent isActive={activeTab === "risks"}>
                    <div className="grid gap-6 lg:grid-cols-12">
                        <div className="space-y-6 lg:col-span-8 xl:col-span-9">
                            {/* Detailed Risk List */}
                            <RiskList
                                projectId={project.id}
                                filterByProbability={matrixFilter?.probability}
                                filterByImpact={matrixFilter?.impact}
                            />
                        </div>
                        <div className="space-y-6 lg:col-span-4 xl:col-span-3">
                            {/* Risk Matrix Heatmap */}
                            <div className="sticky top-8 overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
                                <div className="flex items-center justify-between border-b border-slate-100 bg-white px-6 py-4">
                                    <h3 className="font-semibold text-slate-900">Risk Heatmap</h3>
                                    {matrixFilter && (
                                        <button
                                            onClick={() => setMatrixFilter(null)}
                                            className="flex items-center gap-1 text-xs text-slate-500 transition-colors hover:text-slate-700"
                                        >
                                            <X className="h-3 w-3" />
                                            Clear filter
                                        </button>
                                    )}
                                </div>
                                <div className="flex items-center justify-center p-6">
                                    <RiskMatrix
                                        risks={risks || []}
                                        selectedCell={matrixFilter}
                                        onCellClick={(probability, impact) => {
                                            // Toggle: if clicking the same cell, clear filter
                                            if (
                                                matrixFilter?.probability === probability &&
                                                matrixFilter?.impact === impact
                                            ) {
                                                setMatrixFilter(null);
                                            } else {
                                                setMatrixFilter({ probability, impact });
                                            }
                                        }}
                                    />
                                </div>
                            </div>
                        </div>
                    </div>
                </TabsContent>

                {/* Financials View */}
                {canSeeFinancials && (
                    <TabsContent isActive={activeTab === "financials"}>
                        <div className="grid gap-6 lg:grid-cols-2">
                            <FinancialsCard project={project} />
                            {/* Placeholder for future financial widgets */}
                            <div className="flex items-center justify-center rounded-lg border border-dashed border-slate-300 bg-slate-50 p-6 text-slate-400">
                                <p>Detailed budget breakdown coming soon</p>
                            </div>
                        </div>
                    </TabsContent>
                )}

                {/* Team View */}
                {isCogniterUser && (
                    <TabsContent isActive={activeTab === "team"}>
                        <div className="w-full">
                            <TeamSection projectId={project.id} />
                        </div>
                    </TabsContent>
                )}
            </main>

            <EditProjectModal
                project={project}
                isOpen={isEditModalOpen}
                onClose={() => setIsEditModalOpen(false)}
            />
        </div>
    );
}
