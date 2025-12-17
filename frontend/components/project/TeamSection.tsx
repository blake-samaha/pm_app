"use client";

import { useState } from "react";
import { User, UserRole } from "@/types";
import { useProjectUsers, useRemoveUser } from "@/hooks/useUsers";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Users, UserPlus, X, Loader2, Clock } from "lucide-react";
import { toast } from "sonner";
import { AssignUserModal } from "./AssignUserModal";

interface TeamSectionProps {
    projectId: string;
}

/**
 * Get initials from a name (up to 2 characters)
 */
const getInitials = (name: string): string => {
    const parts = name.trim().split(/\s+/);
    if (parts.length >= 2) {
        return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
    }
    return name.slice(0, 2).toUpperCase();
};

/**
 * Generate a consistent color based on a string (for avatar backgrounds)
 */
const getAvatarColor = (str: string): string => {
    const colors = [
        "bg-blue-500",
        "bg-emerald-500",
        "bg-amber-500",
        "bg-rose-500",
        "bg-violet-500",
        "bg-cyan-500",
        "bg-fuchsia-500",
        "bg-lime-500",
    ];
    let hash = 0;
    for (let i = 0; i < str.length; i++) {
        hash = str.charCodeAt(i) + ((hash << 5) - hash);
    }
    return colors[Math.abs(hash) % colors.length];
};

export const TeamSection = ({ projectId }: TeamSectionProps) => {
    const [isModalOpen, setIsModalOpen] = useState(false);
    const { data: users, isLoading, isError } = useProjectUsers(projectId);
    const removeUser = useRemoveUser();

    const handleRemoveUser = (user: User) => {
        removeUser.mutate(
            { projectId, userId: user.id },
            {
                onSuccess: () => {
                    toast.success("User removed", {
                        description: `${user.name} has been removed from this project.`,
                    });
                },
                onError: (error: any) => {
                    toast.error("Failed to remove user", {
                        description:
                            error.response?.data?.detail ||
                            "An unexpected error occurred.",
                    });
                },
            }
        );
    };

    return (
        <>
            <Card className="overflow-hidden">
                <CardHeader className="border-b bg-gradient-to-r from-slate-50 to-gray-50 py-4">
                    <div className="flex items-center justify-between">
                        <CardTitle className="flex items-center text-lg font-semibold text-gray-800">
                            <Users className="mr-2 h-5 w-5 text-slate-600" />
                            Team
                        </CardTitle>
                        <Button
                            size="sm"
                            variant="outline"
                            onClick={() => setIsModalOpen(true)}
                            className="h-8"
                        >
                            <UserPlus className="mr-1.5 h-3.5 w-3.5" />
                            Add Member
                        </Button>
                    </div>
                </CardHeader>
                <CardContent className="p-0">
                    {isLoading ? (
                        <div className="flex items-center justify-center py-8">
                            <Loader2 className="h-6 w-6 animate-spin text-gray-400" />
                        </div>
                    ) : isError ? (
                        <div className="py-8 text-center text-sm text-red-500">
                            Failed to load team members
                        </div>
                    ) : !users || users.length === 0 ? (
                        <div className="flex flex-col items-center justify-center py-8 text-center">
                            <div className="rounded-full bg-gray-100 p-3">
                                <Users className="h-6 w-6 text-gray-400" />
                            </div>
                            <p className="mt-3 text-sm font-medium text-gray-500">
                                No team members assigned
                            </p>
                            <p className="mt-1 text-xs text-gray-400">
                                Add members to give them access to this project.
                            </p>
                        </div>
                    ) : (
                        <ul className="divide-y divide-gray-100">
                            {users.map((user) => (
                                <li
                                    key={user.id}
                                    className="flex items-center justify-between px-5 py-3 hover:bg-gray-50 transition-colors"
                                >
                                    <div className="flex items-center space-x-3">
                                        <div
                                            className={`flex h-9 w-9 items-center justify-center rounded-full text-sm font-semibold text-white ${getAvatarColor(user.email)}`}
                                        >
                                            {getInitials(user.name)}
                                        </div>
                                        <div>
                                            <div className="flex items-center space-x-2">
                                                <p className="text-sm font-medium text-gray-900">
                                                    {user.name}
                                                </p>
                                                {user.is_pending && (
                                                    <span className="flex items-center rounded-full bg-amber-100 px-1.5 py-0.5 text-[10px] font-medium text-amber-700">
                                                        <Clock className="mr-0.5 h-2.5 w-2.5" />
                                                        Pending
                                                    </span>
                                                )}
                                            </div>
                                            <p className="text-xs text-gray-500">
                                                {user.email}
                                            </p>
                                        </div>
                                    </div>
                                    <div className="flex items-center space-x-2">
                                        <span
                                            className={`rounded-full px-2 py-0.5 text-xs font-medium ${
                                                user.role === UserRole.COGNITER
                                                    ? "bg-blue-100 text-blue-700"
                                                    : "bg-gray-100 text-gray-600"
                                            }`}
                                        >
                                            {user.role}
                                        </span>
                                        <button
                                            onClick={() => handleRemoveUser(user)}
                                            disabled={removeUser.isPending}
                                            className="rounded-full p-1 text-gray-400 hover:bg-gray-200 hover:text-gray-600 transition-colors disabled:opacity-50"
                                            title="Remove from project"
                                        >
                                            {removeUser.isPending ? (
                                                <Loader2 className="h-4 w-4 animate-spin" />
                                            ) : (
                                                <X className="h-4 w-4" />
                                            )}
                                        </button>
                                    </div>
                                </li>
                            ))}
                        </ul>
                    )}
                </CardContent>
            </Card>

            <AssignUserModal
                projectId={projectId}
                isOpen={isModalOpen}
                onClose={() => setIsModalOpen(false)}
                assignedUserIds={users?.map((u) => u.id) || []}
            />
        </>
    );
};

