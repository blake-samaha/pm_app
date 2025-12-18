import { create } from "zustand";
import { persist } from "zustand/middleware";

import type { User } from "@/types";

interface AuthState {
    user: User | null;
    accessToken: string | null;
    isAuthenticated: boolean;
    isSuperuser: boolean;
    impersonatingUserId: string | null;
    impersonatingUser: User | null;
    setAuth: (user: User, token: string, isSuperuser?: boolean) => void;
    setImpersonation: (userId: string | null, user: User | null) => void;
    logout: () => void;
}

export const useAuthStore = create<AuthState>()(
    persist(
        (set) => ({
            user: null,
            accessToken: null,
            isAuthenticated: false,
            isSuperuser: false,
            impersonatingUserId: null,
            impersonatingUser: null,
            setAuth: (user, token, isSuperuser = false) => {
                localStorage.setItem("accessToken", token);
                set({
                    user,
                    accessToken: token,
                    isAuthenticated: true,
                    isSuperuser,
                });
            },
            setImpersonation: (userId, user) => {
                set({
                    impersonatingUserId: userId,
                    impersonatingUser: user,
                });
            },
            logout: () => {
                localStorage.removeItem("accessToken");
                set({
                    user: null,
                    accessToken: null,
                    isAuthenticated: false,
                    isSuperuser: false,
                    impersonatingUserId: null,
                    impersonatingUser: null,
                });
            },
        }),
        {
            name: "auth-storage",
            partialize: (state) => ({
                user: state.user,
                accessToken: state.accessToken,
                isAuthenticated: state.isAuthenticated,
                isSuperuser: state.isSuperuser,
                impersonatingUserId: state.impersonatingUserId,
                impersonatingUser: state.impersonatingUser,
            }),
        }
    )
);
