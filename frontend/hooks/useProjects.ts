import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Project } from "@/types";
import { useAuthStore } from "@/store/authStore";

export const useProjects = () => {
    const { isAuthenticated } = useAuthStore();
    return useQuery({
        queryKey: ["projects"],
        queryFn: async () => {
            const { data } = await api.get<Project[]>("/projects/");
            return data;
        },
        enabled: isAuthenticated,
    });
};

export const useProject = (id: string) => {
    const { isAuthenticated } = useAuthStore();
    return useQuery({
        queryKey: ["projects", id],
        queryFn: async () => {
            const { data } = await api.get<Project>(`/projects/${id}`);
            return data;
        },
        enabled: !!id && isAuthenticated,
    });
};

export const useCreateProject = () => {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: async (newProject: Partial<Project>) => {
            const { data } = await api.post<Project>("/projects/", newProject);
            return data;
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["projects"] });
        },
    });
};

export const useUpdateProject = () => {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: async ({ id, data }: { id: string; data: Partial<Project> }) => {
            const response = await api.patch<Project>(`/projects/${id}`, data);
            return response.data;
        },
        onSuccess: (data) => {
            queryClient.invalidateQueries({ queryKey: ["projects"] });
            queryClient.invalidateQueries({ queryKey: ["projects", data.id] });
        },
    });
};
