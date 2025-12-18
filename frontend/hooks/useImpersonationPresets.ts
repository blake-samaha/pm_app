import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { useAuthStore } from "@/store/authStore";
import type { User } from "@/types";

/**
 * Fetch stable QA personas for superuser impersonation.
 * These are created/ensured by the backend and are safe to use for role cycling.
 */
export const useImpersonationPresets = () => {
    const { isAuthenticated, isSuperuser } = useAuthStore();

    return useQuery({
        queryKey: ["auth", "impersonation-presets"],
        queryFn: async () => {
            const { data } = await api.get<User[]>("/auth/impersonation-presets");
            return data;
        },
        enabled: isAuthenticated && isSuperuser,
    });
};
