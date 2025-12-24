/**
 * Risk hooks - wraps generated API client hooks.
 *
 * This module provides a stable API for components while using
 * contract-driven generated types under the hood.
 */

import { useQueryClient } from "@tanstack/react-query";
import { useAuthStore } from "@/store/authStore";

// Import generated hooks and types
import {
    useReadRisksRisksGet,
    useGetRiskRisksRiskIdGet,
    useCreateRiskRisksPost,
    useDeleteRiskRisksRiskIdDelete,
    useResolveRiskRisksRiskIdResolvePost,
    useReopenRiskRisksRiskIdReopenPost,
    useGetRiskCommentsRisksRiskIdCommentsGet,
    useAddRiskCommentRisksRiskIdCommentsPost,
    getReadRisksRisksGetQueryKey,
    getGetRiskRisksRiskIdGetQueryKey,
    getGetRiskCommentsRisksRiskIdCommentsGetQueryKey,
} from "@/lib/api/generated/risks/risks";

// Re-export generated types for consumers
export type {
    RiskRead,
    RiskCreate,
    RiskResolve,
    RiskReopen,
    RiskStatus,
    RiskImpact,
    RiskProbability,
    CommentRead,
    CommentCreate,
} from "@/lib/api/generated/models";

/**
 * Fetch all risks for a project.
 */
export const useRisks = (projectId: string) => {
    const { isAuthenticated } = useAuthStore();

    return useReadRisksRisksGet(
        { project_id: projectId },
        {
            query: {
                enabled: !!projectId && isAuthenticated,
            },
        }
    );
};

/**
 * Fetch a single risk by ID.
 */
export const useRisk = (riskId: string) => {
    const { isAuthenticated } = useAuthStore();

    return useGetRiskRisksRiskIdGet(riskId, {
        query: {
            enabled: !!riskId && isAuthenticated,
        },
    });
};

/**
 * Create a new risk.
 */
export const useCreateRisk = () => {
    const queryClient = useQueryClient();

    return useCreateRiskRisksPost({
        mutation: {
            onSuccess: (data) => {
                queryClient.invalidateQueries({
                    queryKey: getReadRisksRisksGetQueryKey({ project_id: data.project_id }),
                });
            },
        },
    });
};

/**
 * Resolve a risk.
 */
export const useResolveRisk = () => {
    const queryClient = useQueryClient();

    return useResolveRiskRisksRiskIdResolvePost({
        mutation: {
            onSuccess: (data) => {
                queryClient.invalidateQueries({
                    queryKey: getGetRiskRisksRiskIdGetQueryKey(data.id),
                });
                queryClient.invalidateQueries({
                    queryKey: getReadRisksRisksGetQueryKey({ project_id: data.project_id }),
                });
            },
        },
    });
};

/**
 * Reopen a resolved risk.
 */
export const useReopenRisk = () => {
    const queryClient = useQueryClient();

    return useReopenRiskRisksRiskIdReopenPost({
        mutation: {
            onSuccess: (data) => {
                queryClient.invalidateQueries({
                    queryKey: getGetRiskRisksRiskIdGetQueryKey(data.id),
                });
                queryClient.invalidateQueries({
                    queryKey: getReadRisksRisksGetQueryKey({ project_id: data.project_id }),
                });
            },
        },
    });
};

/**
 * Fetch comments for a risk.
 */
export const useRiskComments = (riskId: string) => {
    const { isAuthenticated } = useAuthStore();

    return useGetRiskCommentsRisksRiskIdCommentsGet(riskId, {
        query: {
            enabled: !!riskId && isAuthenticated,
        },
    });
};

/**
 * Add a comment to a risk.
 */
export const useAddRiskComment = () => {
    const queryClient = useQueryClient();

    return useAddRiskCommentRisksRiskIdCommentsPost({
        mutation: {
            onSuccess: (data, variables) => {
                queryClient.invalidateQueries({
                    queryKey: getGetRiskCommentsRisksRiskIdCommentsGetQueryKey(variables.riskId),
                });
            },
        },
    });
};

/**
 * Delete a risk.
 */
export const useDeleteRisk = () => {
    const queryClient = useQueryClient();

    return useDeleteRiskRisksRiskIdDelete({
        mutation: {
            onSuccess: (_data, variables) => {
                // Invalidate all risk lists (we don't have projectId in the response)
                queryClient.invalidateQueries({
                    predicate: (query) =>
                        Array.isArray(query.queryKey) && query.queryKey[0] === "/risks/",
                });
            },
        },
    });
};
