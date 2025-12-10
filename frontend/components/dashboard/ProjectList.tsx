"use client";

import { useProjects } from "@/hooks/useProjects";
import { ProjectCard } from "./ProjectCard";
import { Loader2 } from "lucide-react";

export const ProjectList = () => {
    const { data: projects, isLoading, error } = useProjects();

    if (isLoading) {
        return (
            <div className="flex h-64 items-center justify-center">
                <Loader2 className="h-8 w-8 animate-spin text-gray-400" />
            </div>
        );
    }

    if (error) {
        return (
            <div className="rounded-lg bg-red-50 p-4 text-red-600">
                Failed to load projects. Please try again.
            </div>
        );
    }

    if (!projects || projects.length === 0) {
        return (
            <div className="flex h-64 flex-col items-center justify-center rounded-xl border-2 border-dashed border-gray-200 bg-gray-50 text-center">
                <h3 className="text-lg font-medium text-gray-900">
                    No projects found
                </h3>
                <p className="mt-1 text-sm text-gray-500">
                    Get started by creating a new project.
                </p>
            </div>
        );
    }

    return (
        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {projects.map((project) => (
                <ProjectCard key={project.id} project={project} />
            ))}
        </div>
    );
};
