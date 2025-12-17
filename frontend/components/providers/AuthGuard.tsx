"use client";

import { useEffect, useState } from "react";
import { useRouter, usePathname } from "next/navigation";
import { useAuthStore } from "@/store/authStore";
import { Loader2 } from "lucide-react";

const PUBLIC_PATHS = ["/login"];

export function AuthGuard({ children }: { children: React.ReactNode }) {
    const router = useRouter();
    const pathname = usePathname();
    const { isAuthenticated, user } = useAuthStore();
    const [isChecking, setIsChecking] = useState(true);

    useEffect(() => {
        // Wait for hydration to complete (handled by Zustand persist)
        // We can check if we are clientside by ensuring window is defined
        if (typeof window !== "undefined") {
            setIsChecking(false);
        }
    }, []);

    useEffect(() => {
        if (isChecking) return;

        const isPublicPath = PUBLIC_PATHS.includes(pathname);

        if (!isAuthenticated && !isPublicPath) {
            router.push("/login");
        } else if (isAuthenticated && isPublicPath) {
            // Redirect to dashboard if already logged in and trying to access login
            router.push("/");
        }
    }, [isAuthenticated, pathname, router, isChecking]);

    // Show loading spinner while checking auth state or redirecting
    if (isChecking) {
        return (
            <div className="flex h-screen w-full items-center justify-center">
                <Loader2 className="h-8 w-8 animate-spin text-gray-400" />
            </div>
        );
    }

    // Don't render protected content until authenticated
    if (!isAuthenticated && !PUBLIC_PATHS.includes(pathname)) {
        return null;
    }

    return <>{children}</>;
}


