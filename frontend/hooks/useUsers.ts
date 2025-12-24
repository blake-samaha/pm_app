import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { User, InviteUserResponse } from "@/lib/api/types";
import { UserRole } from "@/lib/api/types";
import { useAuthStore } from "@/store/authStore";

/**
 * Fetch all users with optional filtering.
 * Requires Cogniter authentication.
 *
 * @param search - Optional search term
 * @param role - Optional role filter
 * @param enabled - Whether to enable the query (default: true). Set to false to prevent
 *                  fetching (useful when modal is closed or search term is too short)
 */
export const useUsers = (search?: string, role?: UserRole, enabled: boolean = true) => {
    const { isAuthenticated } = useAuthStore();

    return useQuery({
        queryKey: ["users", { search, role }],
        queryFn: async () => {
            const params = new URLSearchParams();
            if (search) params.append("search", search);
            if (role) params.append("role", role);
            const queryString = params.toString();
            const url = queryString ? `/users/?${queryString}` : "/users/";
            const { data } = await api.get<User[]>(url);
            return data;
        },
        enabled: isAuthenticated && enabled,
    });
};

/**
 * Fetch users assigned to a specific project.
 */
export const useProjectUsers = (projectId: string, enabled: boolean = true) => {
    const { isAuthenticated } = useAuthStore();

    return useQuery({
        queryKey: ["projects", projectId, "users"],
        queryFn: async () => {
            const { data } = await api.get<User[]>(`/projects/${projectId}/users`);
            return data;
        },
        enabled: !!projectId && isAuthenticated && enabled,
    });
};

/**
 * Mutation to assign a user to a project.
 */
export const useAssignUser = () => {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: async ({ projectId, userId }: { projectId: string; userId: string }) => {
            await api.post(`/projects/${projectId}/users/${userId}`);
        },
        onSuccess: (_, { projectId }) => {
            // Invalidate the project users query to refetch
            queryClient.invalidateQueries({
                queryKey: ["projects", projectId, "users"],
            });
        },
    });
};

/**
 * Mutation to remove a user from a project.
 */
export const useRemoveUser = () => {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: async ({ projectId, userId }: { projectId: string; userId: string }) => {
            await api.delete(`/projects/${projectId}/users/${userId}`);
        },
        onSuccess: (_, { projectId }) => {
            // Invalidate the project users query to refetch
            queryClient.invalidateQueries({
                queryKey: ["projects", projectId, "users"],
            });
        },
    });
};

/**
 * Mutation to invite a user to a project by email.
 * Creates a placeholder user if email doesn't exist.
 */
export const useInviteUser = () => {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: async ({ projectId, email }: { projectId: string; email: string }) => {
            const { data } = await api.post<InviteUserResponse>(`/projects/${projectId}/invite`, {
                email,
            });
            return data;
        },
        onSuccess: (_, { projectId }) => {
            // Invalidate the project users query to refetch
            queryClient.invalidateQueries({
                queryKey: ["projects", projectId, "users"],
            });
            // Also invalidate users list since a new user might have been created
            queryClient.invalidateQueries({
                queryKey: ["users"],
            });
        },
    });
};
