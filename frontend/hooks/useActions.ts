import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { ActionItem, Comment, CommentCreateRequest } from "@/types/actions-risks";
import { useAuthStore } from "@/store/authStore";

export const useActions = (projectId: string) => {
    const { isAuthenticated } = useAuthStore();
    return useQuery({
        queryKey: ["actions", projectId],
        queryFn: async () => {
            const { data } = await api.get<ActionItem[]>(`/actions/?project_id=${projectId}`);
            return data;
        },
        enabled: !!projectId && isAuthenticated,
    });
};

export const useUpdateActionStatus = () => {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: async ({ actionId, status }: { actionId: string; status: string }) => {
            const { data } = await api.patch<ActionItem>(`/actions/${actionId}`, { status });
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

export const useActionComments = (actionId: string) => {
    const { isAuthenticated } = useAuthStore();
    return useQuery({
        queryKey: ["actionComments", actionId],
        queryFn: async () => {
            const { data } = await api.get<Comment[]>(`/actions/${actionId}/comments`);
            return data;
        },
        enabled: !!actionId && isAuthenticated,
    });
};

export const useAddActionComment = () => {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: async ({
            actionId,
            projectId,
            ...commentData
        }: { actionId: string; projectId: string } & CommentCreateRequest) => {
            const { data } = await api.post<Comment>(`/actions/${actionId}/comments`, commentData);
            return { comment: data, projectId };
        },
        onSuccess: ({ comment, projectId }) => {
            // Invalidate the comments for this action
            if (comment.action_item_id) {
                queryClient.invalidateQueries({
                    queryKey: ["actionComments", comment.action_item_id],
                });
            }
            // Invalidate the actions list to update comment_count badge
            queryClient.invalidateQueries({
                queryKey: ["actions", projectId],
            });
        },
    });
};
