import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Risk } from "@/types/actions-risks";
import { useAuthStore } from "@/store/authStore";

export const useRisks = (projectId: string) => {
    const { isAuthenticated } = useAuthStore();
    return useQuery({
        queryKey: ["risks", projectId],
        queryFn: async () => {
            const { data } = await api.get<Risk[]>(
                `/risks/?project_id=${projectId}`
            );
            return data;
        },
        enabled: !!projectId && isAuthenticated,
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

