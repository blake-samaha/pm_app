import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { ActionItem } from "@/types/actions-risks";

export const useActions = (projectId: string) => {
    return useQuery({
        queryKey: ["actions", projectId],
        queryFn: async () => {
            const { data } = await api.get<ActionItem[]>(
                `/actions/?project_id=${projectId}`
            );
            return data;
        },
        enabled: !!projectId,
    });
};

export const useUpdateActionStatus = () => {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: async ({
            actionId,
            status,
        }: {
            actionId: string;
            status: string;
        }) => {
            const { data } = await api.patch<ActionItem>(
                `/actions/${actionId}`,
                { status }
            );
            return data;
        },
        onSuccess: (data) => {
            // Invalidate the actions list for this project to refetch
            queryClient.invalidateQueries({
                queryKey: ["actions", data.project_id],
            });
        },
    });
};

