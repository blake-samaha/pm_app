import { useAuthStore } from "@/store/authStore";
import type { User } from "@/lib/api/types";

/**
 * Returns the user whose perspective the UI should render under.
 *
 * - Normal mode: the authenticated user
 * - Impersonation mode (superuser): the impersonated user
 */
export const useEffectiveUser = (): User | null => {
    const { user, impersonatingUser } = useAuthStore();
    return impersonatingUser ?? user;
};
