/**
 * Action hooks - wraps generated API client hooks.
 *
 * This module provides a stable API for components while using
 * contract-driven generated types under the hood.
 */

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useAuthStore } from "@/store/authStore";
import { api } from "@/lib/api";

// Import generated hooks and types
import {
    useReadActionsActionsGet,
    useGetActionCommentsActionsActionIdCommentsGet,
    useAddActionCommentActionsActionIdCommentsPost,
    getReadActionsActionsGetQueryKey,
    getGetActionCommentsActionsActionIdCommentsGetQueryKey,
} from "@/lib/api/generated/actions/actions";

// Re-export generated types for consumers
export type {
    ActionItemRead,
    ActionItemCreate,
    CommentRead,
    CommentCreate,
    ActionStatus,
} from "@/lib/api/generated/models";

/**
 * Fetch all actions for a project.
 */
export const useActions = (projectId: string) => {
    const { isAuthenticated } = useAuthStore();

    return useReadActionsActionsGet(
        { project_id: projectId },
        {
            query: {
                enabled: !!projectId && isAuthenticated,
                // Transform the response to always return an array (handle both paginated and legacy responses)
                select: (data) => {
                    // If it's an array (legacy response), return as-is
                    if (Array.isArray(data)) {
                        return data;
                    }
                    // If it has items property (paginated response), return items
                    if (data && "items" in data) {
                        return data.items;
                    }
                    return [];
                },
            },
        }
    );
};

/**
 * Update an action's status.
 * Note: Using direct API call since generated hooks may not have update mutation.
 */
export const useUpdateActionStatus = () => {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: async ({ actionId, status }: { actionId: string; status: string }) => {
            const { data } = await api.patch(`/actions/${actionId}`, { status });
            return data;
        },
        onSuccess: (data) => {
            // Invalidate the actions list for this project to refetch
            queryClient.invalidateQueries({
                queryKey: getReadActionsActionsGetQueryKey({ project_id: data.project_id }),
            });
        },
    });
};

/**
 * Fetch comments for an action.
 */
export const useActionComments = (actionId: string) => {
    const { isAuthenticated } = useAuthStore();

    return useGetActionCommentsActionsActionIdCommentsGet(actionId, {
        query: {
            enabled: !!actionId && isAuthenticated,
        },
    });
};

/**
 * Add a comment to an action.
 */
export const useAddActionComment = () => {
    const queryClient = useQueryClient();

    return useAddActionCommentActionsActionIdCommentsPost({
        mutation: {
            onSuccess: (data, variables) => {
                // Invalidate the comments for this action
                queryClient.invalidateQueries({
                    queryKey: getGetActionCommentsActionsActionIdCommentsGetQueryKey(
                        variables.actionId
                    ),
                });
                // Invalidate actions list to update comment_count
                // Note: We need projectId from the caller for full invalidation
                if (data.action_item_id) {
                    queryClient.invalidateQueries({
                        predicate: (query) =>
                            Array.isArray(query.queryKey) && query.queryKey[0] === "/actions/",
                    });
                }
            },
        },
    });
};
