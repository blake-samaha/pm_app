/**
 * Project hooks - wraps generated API client hooks.
 *
 * This module provides a stable API for components while using
 * contract-driven generated types under the hood.
 */

import { useQueryClient } from "@tanstack/react-query";
import { useAuthStore } from "@/store/authStore";

// Import generated hooks and types
import {
    useListProjectsProjectsGet,
    useGetProjectProjectsProjectIdGet,
    useCreateProjectProjectsPost,
    useUpdateProjectProjectsProjectIdPatch,
    getListProjectsProjectsGetQueryKey,
    getGetProjectProjectsProjectIdGetQueryKey,
} from "@/lib/api/generated/projects/projects";

// Re-export generated types for consumers
export type { ProjectRead, ProjectCreate, ProjectUpdate } from "@/lib/api/generated/models";

/**
 * Fetch all projects accessible to the current user.
 */
export const useProjects = () => {
    const { isAuthenticated } = useAuthStore();

    return useListProjectsProjectsGet({
        query: {
            enabled: isAuthenticated,
        },
    });
};

/**
 * Fetch a single project by ID.
 */
export const useProject = (id: string) => {
    const { isAuthenticated } = useAuthStore();

    return useGetProjectProjectsProjectIdGet(id, {
        query: {
            enabled: !!id && isAuthenticated,
        },
    });
};

/**
 * Create a new project.
 */
export const useCreateProject = () => {
    const queryClient = useQueryClient();

    return useCreateProjectProjectsPost({
        mutation: {
            onSuccess: () => {
                queryClient.invalidateQueries({
                    queryKey: getListProjectsProjectsGetQueryKey(),
                });
            },
        },
    });
};

/**
 * Update an existing project.
 */
export const useUpdateProject = () => {
    const queryClient = useQueryClient();

    return useUpdateProjectProjectsProjectIdPatch({
        mutation: {
            onSuccess: (data) => {
                queryClient.invalidateQueries({
                    queryKey: getListProjectsProjectsGetQueryKey(),
                });
                queryClient.invalidateQueries({
                    queryKey: getGetProjectProjectsProjectIdGetQueryKey(data.id),
                });
            },
        },
    });
};
