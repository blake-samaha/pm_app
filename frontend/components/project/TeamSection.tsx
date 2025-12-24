"use client";

import { useState } from "react";
import type { User } from "@/lib/api/types";
import { USER_ROLE } from "@/lib/domain/enums";
import { useProjectUsers, useRemoveUser } from "@/hooks/useUsers";
import { useEffectiveUser } from "@/hooks/useEffectiveUser";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Users, UserPlus, X, Loader2, Clock } from "lucide-react";
import { getAvatarColor, getInitials } from "@/lib/avatar";
import { getErrorMessage } from "@/lib/error";
import { toast } from "sonner";
import { AssignUserModal } from "./AssignUserModal";

interface TeamSectionProps {
    projectId: string;
}

export const TeamSection = ({ projectId }: TeamSectionProps) => {
    const currentUser = useEffectiveUser();
    const [isModalOpen, setIsModalOpen] = useState(false);
    const canManageTeam = !!currentUser && currentUser.role === USER_ROLE.COGNITER;
    const { data: users, isLoading, isError } = useProjectUsers(projectId, canManageTeam);
    const removeUser = useRemoveUser();

    // Only Cogniters can view/manage team assignments (matches backend enforcement)
    if (!canManageTeam) {
        return null;
    }

    const handleRemoveUser = (user: User) => {
        removeUser.mutate(
            { projectId, userId: user.id },
            {
                onSuccess: () => {
                    toast.success("User removed", {
                        description: `${user.name} has been removed from this project.`,
                    });
                },
                onError: (error: unknown) => {
                    toast.error("Failed to remove user", {
                        description: getErrorMessage(error),
                    });
                },
            }
        );
    };

    return (
        <>
            <Card className="overflow-hidden">
                <CardHeader className="border-b bg-gradient-to-r from-slate-50/80 to-slate-100/50 py-4">
                    <div className="flex items-center justify-between">
                        <CardTitle className="flex items-center text-lg font-bold text-slate-800">
                            <Users className="mr-2 h-5 w-5 text-slate-600" />
                            Team
                        </CardTitle>
                        <Button
                            size="sm"
                            variant="outline"
                            onClick={() => setIsModalOpen(true)}
                            className="h-8 border-slate-200 bg-white text-slate-700 hover:bg-slate-50"
                        >
                            <UserPlus className="mr-1.5 h-3.5 w-3.5" />
                            Add Member
                        </Button>
                    </div>
                </CardHeader>
                <CardContent className="p-0">
                    {isLoading ? (
                        <div className="flex items-center justify-center py-8">
                            <Loader2 className="h-6 w-6 animate-spin text-slate-400" />
                        </div>
                    ) : isError ? (
                        <div className="py-8 text-center text-sm text-red-500">
                            Failed to load team members
                        </div>
                    ) : !users || users.length === 0 ? (
                        <div className="flex flex-col items-center justify-center py-10 text-center">
                            <div className="rounded-full border border-slate-100 bg-slate-50 p-4">
                                <Users className="h-6 w-6 text-slate-300" />
                            </div>
                            <p className="mt-4 text-sm font-semibold text-slate-900">
                                No team members assigned
                            </p>
                            <p className="mt-1 text-xs text-slate-500">
                                Add members to give them access to this project.
                            </p>
                        </div>
                    ) : (
                        <ul className="divide-y divide-slate-100">
                            {users.map((user) => (
                                <li
                                    key={user.id}
                                    className="flex items-center justify-between px-6 py-4 transition-colors hover:bg-slate-50/50"
                                >
                                    <div className="flex items-center space-x-4">
                                        <div
                                            className={`flex h-9 w-9 items-center justify-center rounded-full text-sm font-bold text-white shadow-sm ring-2 ring-white ${getAvatarColor(user.email)}`}
                                        >
                                            {getInitials(user.name)}
                                        </div>
                                        <div>
                                            <div className="flex items-center space-x-2">
                                                <p className="text-sm font-semibold text-slate-900">
                                                    {user.name}
                                                </p>
                                                {user.is_pending && (
                                                    <span className="flex items-center rounded-full border border-amber-100 bg-amber-50 px-2 py-0.5 text-[10px] font-bold text-amber-700">
                                                        <Clock className="mr-1 h-2.5 w-2.5" />
                                                        Pending
                                                    </span>
                                                )}
                                            </div>
                                            <p className="text-xs font-medium text-slate-500">
                                                {user.email}
                                            </p>
                                        </div>
                                    </div>
                                    <div className="flex items-center space-x-3">
                                        <span
                                            className={`rounded-md px-2.5 py-1 text-[10px] font-bold uppercase tracking-wider ${
                                                user.role === USER_ROLE.COGNITER
                                                    ? "border border-blue-100 bg-blue-50 text-blue-700"
                                                    : "border border-slate-200 bg-slate-100 text-slate-600"
                                            }`}
                                        >
                                            {user.role}
                                        </span>
                                        <button
                                            onClick={() => handleRemoveUser(user)}
                                            disabled={removeUser.isPending}
                                            className="rounded-full p-1.5 text-slate-400 transition-colors hover:bg-red-50 hover:text-red-600 disabled:opacity-50"
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
