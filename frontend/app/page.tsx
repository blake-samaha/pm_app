"use client";

import { useAuthStore } from "@/store/authStore";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { ProjectList } from "@/components/dashboard/ProjectList";
import { CreateProjectModal } from "@/components/dashboard/CreateProjectModal";
import { Plus } from "lucide-react";

export default function Home() {
    const { user, isAuthenticated, logout } = useAuthStore();
    const router = useRouter();
    const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);

    useEffect(() => {
        if (!isAuthenticated) {
            router.push("/login");
        }
    }, [isAuthenticated, router]);

    if (!isAuthenticated) {
        return null;
    }

    return (
        <main className="min-h-screen bg-gray-50">
            {/* Header */}
            <header className="bg-white shadow-sm">
                <div className="mx-auto flex max-w-screen-2xl items-center justify-between px-4 py-4 sm:px-6 lg:px-8">
                    <div className="flex items-center space-x-4">
                        <h1 className="text-2xl font-bold text-gray-900">
                            Projects
                        </h1>
                    </div>

                    <div className="flex items-center space-x-4">
                        <div className="flex items-center space-x-2">
                            {user?.role === "Cogniter" && (
                                <span className="rounded-full bg-blue-100 px-3 py-1 text-xs font-medium text-blue-800">
                                    Internal
                                </span>
                            )}
                            <span className="text-sm font-medium text-gray-700">
                                {user?.name}
                            </span>
                            <button
                                onClick={() => {
                                    logout();
                                    router.push("/login");
                                }}
                                className="text-sm text-gray-500 hover:text-gray-700"
                            >
                                Logout
                            </button>
                        </div>
                    </div>
                </div>
            </header>

            {/* Main Content */}
            <div className="mx-auto max-w-screen-2xl px-4 py-8 sm:px-6 lg:px-8">
                <div className="mb-8 flex items-center justify-between">
                    <div>
                        <h2 className="text-lg font-medium text-gray-900">
                            Active Projects
                        </h2>
                        <p className="mt-1 text-sm text-gray-500">
                            Overview of all ongoing projects and their status.
                        </p>
                    </div>

                    {user?.role === "Cogniter" && (
                        <button
                            onClick={() => setIsCreateModalOpen(true)}
                            className="flex items-center rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-blue-700"
                        >
                            <Plus className="mr-2 h-4 w-4" />
                            New Project
                        </button>
                    )}
                </div>

                <ProjectList />
            </div>

            <CreateProjectModal
                isOpen={isCreateModalOpen}
                onClose={() => setIsCreateModalOpen(false)}
            />
        </main>
    );
}
