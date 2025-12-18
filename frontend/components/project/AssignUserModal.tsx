"use client";

import { useState, useMemo, useEffect } from "react";
import { User, UserRole } from "@/types";
import { useUsers, useAssignUser, useInviteUser } from "@/hooks/useUsers";
import { Button } from "@/components/ui/button";
import { X, Search, UserPlus, Loader2, Users, Mail, Clock } from "lucide-react";
import { toast } from "sonner";

interface AssignUserModalProps {
    projectId: string;
    isOpen: boolean;
    onClose: () => void;
    assignedUserIds: string[];
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

/**
 * Simple email validation
 */
const isValidEmail = (email: string): boolean => {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.trim());
};

export const AssignUserModal = ({
    projectId,
    isOpen,
    onClose,
    assignedUserIds,
}: AssignUserModalProps) => {
    const [searchTerm, setSearchTerm] = useState("");
    const [debouncedSearch, setDebouncedSearch] = useState("");
    const [assigningUserId, setAssigningUserId] = useState<string | null>(null);
    const [isInviting, setIsInviting] = useState(false);

    // Debounce search input
    useEffect(() => {
        const timer = setTimeout(() => {
            setDebouncedSearch(searchTerm);
        }, 300);
        return () => clearTimeout(timer);
    }, [searchTerm]);

    // Reset search when modal closes
    useEffect(() => {
        if (!isOpen) {
            setSearchTerm("");
            setDebouncedSearch("");
        }
    }, [isOpen]);

    const { data: allUsers, isLoading } = useUsers(debouncedSearch || undefined, undefined);
    const assignUser = useAssignUser();
    const inviteUser = useInviteUser();

    // Filter out already assigned users
    const availableUsers = useMemo(() => {
        if (!allUsers) return [];
        return allUsers.filter((user) => !assignedUserIds.includes(user.id));
    }, [allUsers, assignedUserIds]);

    // Check if the search term looks like an email that isn't in the results
    const canInviteByEmail = useMemo(() => {
        if (!isValidEmail(searchTerm)) return false;
        // Check if this email is already in the user list
        const emailLower = searchTerm.toLowerCase().trim();
        const emailInResults = allUsers?.some((user) => user.email.toLowerCase() === emailLower);
        return !emailInResults;
    }, [searchTerm, allUsers]);

    const handleAssign = (user: User) => {
        setAssigningUserId(user.id);
        assignUser.mutate(
            { projectId, userId: user.id },
            {
                onSuccess: () => {
                    toast.success("User assigned", {
                        description: `${user.name} now has access to this project.`,
                    });
                    setAssigningUserId(null);
                },
                onError: (error: any) => {
                    toast.error("Failed to assign user", {
                        description:
                            error.response?.data?.detail || "An unexpected error occurred.",
                    });
                    setAssigningUserId(null);
                },
            }
        );
    };

    const handleInviteByEmail = () => {
        const email = searchTerm.trim().toLowerCase();
        setIsInviting(true);
        inviteUser.mutate(
            { projectId, email },
            {
                onSuccess: (response) => {
                    if (response.was_created) {
                        toast.success("Invitation sent", {
                            description: response.message,
                        });
                    } else {
                        toast.success("User assigned", {
                            description: response.message,
                        });
                    }
                    setSearchTerm("");
                    setIsInviting(false);
                },
                onError: (error: any) => {
                    toast.error("Failed to invite user", {
                        description:
                            error.response?.data?.detail || "An unexpected error occurred.",
                    });
                    setIsInviting(false);
                },
            }
        );
    };

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4 backdrop-blur-sm">
            <div className="w-full max-w-md overflow-hidden rounded-xl bg-white shadow-2xl">
                {/* Header */}
                <div className="flex items-center justify-between border-b px-6 py-4">
                    <h2 className="flex items-center text-lg font-semibold text-gray-900">
                        <UserPlus className="mr-2 h-5 w-5 text-gray-600" />
                        Assign Team Member
                    </h2>
                    <button
                        onClick={onClose}
                        className="rounded-full p-1 text-gray-400 hover:bg-gray-100 hover:text-gray-500"
                    >
                        <X className="h-5 w-5" />
                    </button>
                </div>

                {/* Search */}
                <div className="border-b px-6 py-3">
                    <div className="relative">
                        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
                        <input
                            type="text"
                            placeholder="Search by name or email..."
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                            className="w-full rounded-md border border-gray-300 py-2 pl-10 pr-4 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                            autoFocus
                        />
                    </div>
                </div>

                {/* User List */}
                <div className="max-h-80 overflow-y-auto">
                    {isLoading ? (
                        <div className="flex items-center justify-center py-12">
                            <Loader2 className="h-6 w-6 animate-spin text-gray-400" />
                        </div>
                    ) : availableUsers.length === 0 && !canInviteByEmail ? (
                        <div className="flex flex-col items-center justify-center px-6 py-12 text-center">
                            <div className="rounded-full bg-gray-100 p-3">
                                <Users className="h-6 w-6 text-gray-400" />
                            </div>
                            <p className="mt-3 text-sm font-medium text-gray-500">
                                {searchTerm
                                    ? "No users found matching your search"
                                    : "No available users to assign"}
                            </p>
                            <p className="mt-1 text-xs text-gray-400">
                                {searchTerm
                                    ? "Enter a valid email to invite a new user"
                                    : "All users are already assigned to this project"}
                            </p>
                        </div>
                    ) : (
                        <ul className="divide-y divide-gray-100">
                            {/* Invite by email option */}
                            {canInviteByEmail && (
                                <li className="flex items-center justify-between border-b border-blue-100 bg-blue-50 px-6 py-3">
                                    <div className="flex items-center space-x-3">
                                        <div className="flex h-9 w-9 items-center justify-center rounded-full bg-blue-500 text-sm font-semibold text-white">
                                            <Mail className="h-4 w-4" />
                                        </div>
                                        <div>
                                            <p className="text-sm font-medium text-gray-900">
                                                Invite new user
                                            </p>
                                            <p className="text-xs text-blue-600">
                                                {searchTerm.trim().toLowerCase()}
                                            </p>
                                        </div>
                                    </div>
                                    <Button
                                        size="sm"
                                        onClick={handleInviteByEmail}
                                        disabled={isInviting}
                                        className="h-8 bg-blue-600 hover:bg-blue-700"
                                    >
                                        {isInviting ? (
                                            <Loader2 className="h-4 w-4 animate-spin" />
                                        ) : (
                                            <>
                                                <Mail className="mr-1 h-3.5 w-3.5" />
                                                Invite
                                            </>
                                        )}
                                    </Button>
                                </li>
                            )}
                            {/* Existing users */}
                            {availableUsers.map((user) => (
                                <li
                                    key={user.id}
                                    className="flex items-center justify-between px-6 py-3 transition-colors hover:bg-gray-50"
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
                                            <div className="flex items-center space-x-2">
                                                <p className="text-xs text-gray-500">
                                                    {user.email}
                                                </p>
                                                <span
                                                    className={`rounded-full px-1.5 py-0.5 text-[10px] font-medium ${
                                                        user.role === UserRole.COGNITER
                                                            ? "bg-blue-100 text-blue-700"
                                                            : "bg-gray-100 text-gray-600"
                                                    }`}
                                                >
                                                    {user.role}
                                                </span>
                                            </div>
                                        </div>
                                    </div>
                                    <Button
                                        size="sm"
                                        onClick={() => handleAssign(user)}
                                        disabled={assigningUserId === user.id}
                                        className="h-8"
                                    >
                                        {assigningUserId === user.id ? (
                                            <Loader2 className="h-4 w-4 animate-spin" />
                                        ) : (
                                            <>
                                                <UserPlus className="mr-1 h-3.5 w-3.5" />
                                                Assign
                                            </>
                                        )}
                                    </Button>
                                </li>
                            ))}
                        </ul>
                    )}
                </div>

                {/* Footer */}
                <div className="border-t px-6 py-4">
                    <Button variant="outline" onClick={onClose} className="w-full">
                        Close
                    </Button>
                </div>
            </div>
        </div>
    );
};
