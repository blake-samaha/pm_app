"use client";

import { useParams, useRouter } from "next/navigation";
import { useEffect } from "react";
import { useProject } from "@/hooks/useProjects";
import { useAuthStore } from "@/store/authStore";
import { HealthIndicator } from "@/components/project/HealthIndicator";
import { FinancialsCard } from "@/components/project/FinancialsCard";
import { Timeline } from "@/components/project/Timeline";
import { ActionTable } from "@/components/project/ActionTable";
import { RiskList } from "@/components/project/RiskList";
import { SyncButton } from "@/components/project/SyncButton";
import { ArrowLeft, Loader2, ExternalLink } from "lucide-react";
import Link from "next/link";

export default function ProjectDetailsPage() {
    const params = useParams();
    const router = useRouter();
    const { user, isAuthenticated } = useAuthStore();
    const projectId = params.id as string;

    const { data: project, isLoading, error } = useProject(projectId);

    useEffect(() => {
        if (!isAuthenticated) {
            router.push("/login");
        }
    }, [isAuthenticated, router]);

    if (!isAuthenticated) {
        return null;
    }

    if (isLoading) {
        return (
            <div className="flex min-h-screen items-center justify-center">
                <Loader2 className="h-8 w-8 animate-spin text-gray-400" />
            </div>
        );
    }

    if (error || !project) {
        return (
            <div className="flex min-h-screen flex-col items-center justify-center">
                <p className="text-red-600">
                    {error ? "Failed to load project" : "Project not found"}
                </p>
                <Link href="/" className="mt-4 text-blue-600 hover:underline">
                    Back to Dashboard
                </Link>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gray-50 pb-12">
            {/* Header */}
            <header className="bg-white shadow-sm">
                <div className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
                    <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-4">
                            <Link
                                href="/"
                                className="text-gray-400 hover:text-gray-600"
                            >
                                <ArrowLeft className="h-6 w-6" />
                            </Link>
                            <div>
                                <h1 className="text-2xl font-bold text-gray-900">
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

                        <div className="flex items-center space-x-6">
                            {user?.role === "Cogniter" && (
                                <SyncButton projectId={project.id} />
                            )}
                            <div className="text-right">
                                <p className="text-xs font-medium uppercase tracking-wider text-gray-500">
                                    Overall Health
                                </p>
                                <div className="mt-1">
                                    <HealthIndicator
                                        status={
                                            project.health_status_override ||
                                            project.health_status
                                        }
                                        label={
                                            project.health_status_override ||
                                            project.health_status
                                        }
                                    />
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </header>

            <main className="mx-auto mt-8 max-w-7xl px-4 sm:px-6 lg:px-8">
                <div className="grid gap-8 lg:grid-cols-3">
                    {/* Left Column (2/3 width) */}
                    <div className="space-y-8 lg:col-span-2">
                        <Timeline project={project} />
                        <ActionTable projectId={project.id} />
                    </div>

                    {/* Right Column (1/3 width) */}
                    <div className="space-y-8">
                        <FinancialsCard project={project} />
                        <RiskList projectId={project.id} />
                    </div>
                </div>
            </main>
        </div>
    );
}
