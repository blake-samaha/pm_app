"use client";

import { useState } from "react";
import { api } from "@/lib/api";
import { RefreshCw } from "lucide-react";
import { toast } from "sonner";

interface SyncButtonProps {
    projectId: string;
}

export const SyncButton = ({ projectId }: SyncButtonProps) => {
    const [syncing, setSyncing] = useState(false);

    const handleSync = async () => {
        setSyncing(true);
        try {
            await api.post(`/sync/${projectId}`);
            toast.success("Sync started", {
                description: "Data synchronization is running in the background.",
            });
        } catch (err) {
            console.error("Sync failed", err);
            toast.error("Sync failed", {
                description: "Unable to trigger data sync. Please try again.",
            });
        } finally {
            setSyncing(false);
        }
    };

    return (
        <button
            onClick={handleSync}
            disabled={syncing}
            className="flex items-center rounded-md bg-white px-3 py-2 text-sm font-medium text-gray-700 shadow-sm hover:bg-gray-50 disabled:opacity-50"
        >
            <RefreshCw className={`mr-2 h-4 w-4 ${syncing ? "animate-spin" : ""}`} />
            {syncing ? "Syncing..." : "Sync Data"}
        </button>
    );
};
