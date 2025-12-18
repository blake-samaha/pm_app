"use client";

import { useAuthStore } from "@/store/authStore";
import { useUsers } from "@/hooks/useUsers";
import { useImpersonationPresets } from "@/hooks/useImpersonationPresets";
import { ChevronDown, Eye, X } from "lucide-react";
import { useState, useRef, useEffect } from "react";

export function ImpersonationBar() {
    const { isSuperuser, impersonatingUser, impersonatingUserId, setImpersonation } =
        useAuthStore();
    const {
        data: users,
        isLoading: usersLoading,
        isError: usersIsError,
        error: usersError,
    } = useUsers();
    const {
        data: presets,
        isLoading: presetsLoading,
        isError: presetsIsError,
        error: presetsError,
    } = useImpersonationPresets();
    const [isOpen, setIsOpen] = useState(false);
    const dropdownRef = useRef<HTMLDivElement>(null);

    // Close dropdown when clicking outside
    useEffect(() => {
        function handleClickOutside(event: MouseEvent) {
            if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
                setIsOpen(false);
            }
        }
        document.addEventListener("mousedown", handleClickOutside);
        return () => document.removeEventListener("mousedown", handleClickOutside);
    }, []);

    // Only render for superusers
    if (!isSuperuser) return null;

    // Height of the impersonation bar (for the spacer)
    const barHeight = "44px";
    const presetIds = new Set((presets || []).map((u) => u.id));

    const handleSelectUser = (userId: string | null) => {
        if (userId === null) {
            setImpersonation(null, null);
        } else {
            const candidates = [...(presets || []), ...(users || [])];
            const user = candidates.find((u) => u.id === userId);
            if (user) {
                setImpersonation(userId, user);
            }
        }
        setIsOpen(false);
        // Reload the page to refresh all data with new perspective
        window.location.reload();
    };

    const stopImpersonating = () => {
        setImpersonation(null, null);
        window.location.reload();
    };

    return (
        <>
            {/* Spacer to push content down */}
            <div style={{ height: barHeight }} />
            <div className="fixed left-0 right-0 top-0 z-[9999] bg-amber-500 px-4 py-2 text-black shadow-lg">
                <div className="mx-auto flex max-w-7xl items-center justify-between">
                    {/* Left side: Superuser badge and dropdown */}
                    <div className="flex items-center gap-4">
                        <span className="flex items-center gap-2 text-sm font-bold">
                            <span className="rounded bg-black px-2 py-0.5 text-xs text-amber-500">
                                SUPERUSER
                            </span>
                        </span>

                        {/* User selection dropdown */}
                        <div className="relative" ref={dropdownRef}>
                            <button
                                onClick={() => setIsOpen(!isOpen)}
                                disabled={usersLoading || presetsLoading}
                                className="flex items-center gap-2 rounded-lg border border-amber-600 bg-white/90 px-3 py-1.5 text-sm font-medium transition-colors hover:bg-white"
                            >
                                <Eye className="h-4 w-4" />
                                <span>
                                    {impersonatingUser
                                        ? `Viewing as: ${impersonatingUser.name}`
                                        : "View as another user"}
                                </span>
                                <ChevronDown
                                    className={`h-4 w-4 transition-transform ${isOpen ? "rotate-180" : ""}`}
                                />
                            </button>

                            {isOpen && (
                                <div className="absolute left-0 top-full mt-1 w-72 overflow-hidden rounded-lg border border-gray-200 bg-white shadow-xl">
                                    <div className="max-h-64 overflow-y-auto">
                                        {/* Option to view as self */}
                                        <button
                                            onClick={() => handleSelectUser(null)}
                                            className={`flex w-full items-center gap-2 px-4 py-2 text-left text-sm hover:bg-gray-100 ${
                                                !impersonatingUserId
                                                    ? "bg-amber-50 font-medium"
                                                    : ""
                                            }`}
                                        >
                                            <span className="h-2 w-2 rounded-full bg-green-500" />
                                            Myself (Superuser)
                                        </button>

                                        {/* Preset personas for quick role QA */}
                                        <div className="border-t border-gray-100" />
                                        <div className="px-4 py-2 text-[11px] font-semibold uppercase tracking-wider text-gray-500">
                                            Quick role views
                                        </div>

                                        {presetsLoading && (
                                            <div className="px-4 py-3 text-center text-sm text-gray-500">
                                                Loading presets...
                                            </div>
                                        )}

                                        {presetsIsError && (
                                            <div className="px-4 py-3 text-sm text-red-600">
                                                Failed to load presets:{" "}
                                                {(presetsError as any)?.message || "Unknown error"}
                                            </div>
                                        )}

                                        {!presetsLoading &&
                                            !presetsIsError &&
                                            presets?.map((user) => (
                                                <button
                                                    key={user.id}
                                                    onClick={() => handleSelectUser(user.id)}
                                                    className={`flex w-full items-center justify-between px-4 py-2 text-left text-sm hover:bg-gray-100 ${
                                                        impersonatingUserId === user.id
                                                            ? "bg-amber-50 font-medium"
                                                            : ""
                                                    }`}
                                                >
                                                    <div>
                                                        <div className="font-medium">
                                                            {user.name}
                                                        </div>
                                                        <div className="text-xs text-gray-500">
                                                            {user.email}
                                                        </div>
                                                    </div>
                                                    <span
                                                        className={`rounded-full px-2 py-0.5 text-xs ${
                                                            user.role === "Cogniter"
                                                                ? "bg-blue-100 text-blue-700"
                                                                : user.role ===
                                                                    "Client + Financials"
                                                                  ? "bg-purple-100 text-purple-700"
                                                                  : "bg-gray-100 text-gray-700"
                                                        }`}
                                                    >
                                                        {user.role}
                                                    </span>
                                                </button>
                                            ))}

                                        <div className="border-t border-gray-100" />

                                        {/* List of users */}
                                        {users
                                            ?.filter((u) => !presetIds.has(u.id))
                                            .map((user) => (
                                                <button
                                                    key={user.id}
                                                    onClick={() => handleSelectUser(user.id)}
                                                    className={`flex w-full items-center justify-between px-4 py-2 text-left text-sm hover:bg-gray-100 ${
                                                        impersonatingUserId === user.id
                                                            ? "bg-amber-50 font-medium"
                                                            : ""
                                                    }`}
                                                >
                                                    <div>
                                                        <div className="font-medium">
                                                            {user.name}
                                                        </div>
                                                        <div className="text-xs text-gray-500">
                                                            {user.email}
                                                        </div>
                                                    </div>
                                                    <span
                                                        className={`rounded-full px-2 py-0.5 text-xs ${
                                                            user.role === "Cogniter"
                                                                ? "bg-blue-100 text-blue-700"
                                                                : user.role ===
                                                                    "Client + Financials"
                                                                  ? "bg-purple-100 text-purple-700"
                                                                  : "bg-gray-100 text-gray-700"
                                                        }`}
                                                    >
                                                        {user.role}
                                                    </span>
                                                </button>
                                            ))}

                                        {usersLoading && (
                                            <div className="px-4 py-3 text-center text-sm text-gray-500">
                                                Loading users...
                                            </div>
                                        )}

                                        {usersIsError && (
                                            <div className="px-4 py-3 text-sm text-red-600">
                                                Failed to load users:{" "}
                                                {(usersError as any)?.message || "Unknown error"}
                                            </div>
                                        )}

                                        {!usersLoading &&
                                            !usersIsError &&
                                            (!users || users.length === 0) && (
                                                <div className="px-4 py-3 text-center text-sm text-gray-500">
                                                    No users found
                                                </div>
                                            )}
                                    </div>
                                </div>
                            )}
                        </div>
                    </div>

                    {/* Right side: Active impersonation indicator */}
                    {impersonatingUser && (
                        <div className="flex items-center gap-2">
                            <div className="flex items-center gap-2 rounded-lg bg-red-600 px-3 py-1 text-sm font-medium text-white">
                                <Eye className="h-4 w-4" />
                                <span>
                                    Viewing as: {impersonatingUser.name} ({impersonatingUser.role})
                                </span>
                            </div>
                            <button
                                onClick={stopImpersonating}
                                className="rounded-lg bg-red-700 p-1.5 text-white transition-colors hover:bg-red-800"
                                title="Stop impersonating"
                            >
                                <X className="h-4 w-4" />
                            </button>
                        </div>
                    )}
                </div>
            </div>
        </>
    );
}
