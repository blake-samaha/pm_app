"use client";

import { useRouter } from "next/navigation";
import { useAuthStore } from "@/store/authStore";
import { useEffectiveUser } from "@/hooks/useEffectiveUser";
import { CommandMenuUI } from "@/components/ui/command-menu";

/**
 * CommandMenu container component.
 *
 * This component handles business logic (auth, routing) and passes
 * data/callbacks to the pure CommandMenuUI component.
 */
export function CommandMenu() {
    const router = useRouter();
    const { logout } = useAuthStore();
    const user = useEffectiveUser();

    const handleLogout = () => {
        logout();
        router.push("/login");
    };

    const handleNavigate = (path: string) => {
        router.push(path);
    };

    return (
        <CommandMenuUI
            userName={user?.name ?? null}
            onLogout={handleLogout}
            onNavigate={handleNavigate}
        />
    );
}
