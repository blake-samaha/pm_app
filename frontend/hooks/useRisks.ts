import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import {
    Risk,
    Comment,
    RiskResolveRequest,
    RiskReopenRequest,
    CommentCreateRequest,
} from "@/types/actions-risks";
import { useAuthStore } from "@/store/authStore";

export const useRisks = (projectId: string) => {
    const { isAuthenticated } = useAuthStore();
    return useQuery({
        queryKey: ["risks", projectId],
        queryFn: async () => {
            const { data } = await api.get<Risk[]>(`/risks/?project_id=${projectId}`);
            return data;
        },
        enabled: !!projectId && isAuthenticated,
    });
};

export const useRisk = (riskId: string) => {
    const { isAuthenticated } = useAuthStore();
    return useQuery({
        queryKey: ["risk", riskId],
        queryFn: async () => {
            const { data } = await api.get<Risk>(`/risks/${riskId}`);
            return data;
        },
        enabled: !!riskId && isAuthenticated,
    });
};

export const useCreateRisk = () => {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: async (newRisk: Partial<Risk>) => {
            const { data } = await api.post<Risk>("/risks/", newRisk);
            return data;
        },
        onSuccess: (data) => {
            queryClient.invalidateQueries({
                queryKey: ["risks", data.project_id],
            });
        },
    });
};

export const useResolveRisk = () => {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: async ({ riskId, ...resolveData }: { riskId: string } & RiskResolveRequest) => {
            const { data } = await api.post<Risk>(`/risks/${riskId}/resolve`, resolveData);
            return data;
        },
        onSuccess: (data) => {
            // Invalidate both the specific risk and the list
            queryClient.invalidateQueries({ queryKey: ["risk", data.id] });
            queryClient.invalidateQueries({ queryKey: ["risks", data.project_id] });
        },
    });
};

export const useReopenRisk = () => {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: async ({ riskId, ...reopenData }: { riskId: string } & RiskReopenRequest) => {
            const { data } = await api.post<Risk>(`/risks/${riskId}/reopen`, reopenData);
            return data;
        },
        onSuccess: (data) => {
            queryClient.invalidateQueries({ queryKey: ["risk", data.id] });
            queryClient.invalidateQueries({ queryKey: ["risks", data.project_id] });
        },
    });
};

export const useRiskComments = (riskId: string) => {
    const { isAuthenticated } = useAuthStore();
    return useQuery({
        queryKey: ["riskComments", riskId],
        queryFn: async () => {
            const { data } = await api.get<Comment[]>(`/risks/${riskId}/comments`);
            return data;
        },
        enabled: !!riskId && isAuthenticated,
    });
};

export const useAddRiskComment = () => {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: async ({
            riskId,
            ...commentData
        }: { riskId: string } & CommentCreateRequest) => {
            const { data } = await api.post<Comment>(`/risks/${riskId}/comments`, commentData);
            return data;
        },
        onSuccess: (data) => {
            if (data.risk_id) {
                queryClient.invalidateQueries({ queryKey: ["riskComments", data.risk_id] });
            }
        },
    });
};

export const useDeleteRisk = () => {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: async ({ riskId, projectId }: { riskId: string; projectId: string }) => {
            await api.delete(`/risks/${riskId}`);
            return { riskId, projectId };
        },
        onSuccess: ({ projectId }) => {
            queryClient.invalidateQueries({ queryKey: ["risks", projectId] });
        },
    });
};
