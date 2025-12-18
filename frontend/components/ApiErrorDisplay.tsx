"use client";

import { AlertCircle, ChevronDown, ChevronUp, Copy, RefreshCw } from "lucide-react";
import { useState } from "react";

interface ApiError {
    detail: string;
    error_type?: string;
    status_code?: number;
    traceback?: string[];
}

interface ApiErrorDisplayProps {
    error: ApiError | Error | string;
    title?: string;
    onRetry?: () => void;
    className?: string;
}

/**
 * Component to display API errors with detailed information in development mode.
 * Shows user-friendly messages in production.
 */
export function ApiErrorDisplay({
    error,
    title = "Request Failed",
    onRetry,
    className = "",
}: ApiErrorDisplayProps) {
    const [showDetails, setShowDetails] = useState(false);
    const [copied, setCopied] = useState(false);
    const isDev = process.env.NODE_ENV === "development";

    // Normalize error to ApiError format
    const normalizedError: ApiError = (() => {
        if (typeof error === "string") {
            return { detail: error };
        }
        if (error instanceof Error) {
            return { detail: error.message };
        }
        return error;
    })();

    const handleCopy = async () => {
        const errorText = JSON.stringify(normalizedError, null, 2);
        try {
            await navigator.clipboard.writeText(errorText);
            setCopied(true);
            setTimeout(() => setCopied(false), 2000);
        } catch (err) {
            console.error("Failed to copy:", err);
        }
    };

    const getStatusColor = (status?: number) => {
        if (!status) return "bg-red-50 border-red-200";
        if (status >= 500) return "bg-red-50 border-red-200";
        if (status >= 400) return "bg-orange-50 border-orange-200";
        return "bg-gray-50 border-gray-200";
    };

    const getStatusTextColor = (status?: number) => {
        if (!status) return "text-red-700";
        if (status >= 500) return "text-red-700";
        if (status >= 400) return "text-orange-700";
        return "text-gray-700";
    };

    return (
        <div
            className={`rounded-lg border ${getStatusColor(normalizedError.status_code)} ${className}`}
        >
            {/* Header */}
            <div className="flex items-start gap-3 px-4 py-3">
                <AlertCircle
                    className={`mt-0.5 h-5 w-5 flex-shrink-0 ${getStatusTextColor(normalizedError.status_code)}`}
                />
                <div className="min-w-0 flex-1">
                    <div className="flex flex-wrap items-center gap-2">
                        <h3
                            className={`font-medium ${getStatusTextColor(normalizedError.status_code)}`}
                        >
                            {title}
                        </h3>
                        {normalizedError.status_code && (
                            <span className="rounded-full bg-gray-200 px-2 py-0.5 text-xs text-gray-600">
                                {normalizedError.status_code}
                            </span>
                        )}
                        {normalizedError.error_type && isDev && (
                            <span className="rounded-full bg-gray-800 px-2 py-0.5 font-mono text-xs text-gray-200">
                                {normalizedError.error_type}
                            </span>
                        )}
                    </div>
                    <p
                        className={`mt-1 text-sm ${getStatusTextColor(normalizedError.status_code)}`}
                    >
                        {normalizedError.detail}
                    </p>
                </div>
            </div>

            {/* Expandable traceback (dev only) */}
            {isDev && normalizedError.traceback && normalizedError.traceback.length > 0 && (
                <div className="border-t border-gray-200">
                    <button
                        onClick={() => setShowDetails(!showDetails)}
                        className="flex w-full items-center justify-between px-4 py-2 transition-colors hover:bg-gray-100/50"
                    >
                        <span className="text-xs font-medium text-gray-600">
                            Stack Trace ({normalizedError.traceback.length} frames)
                        </span>
                        {showDetails ? (
                            <ChevronUp className="h-4 w-4 text-gray-400" />
                        ) : (
                            <ChevronDown className="h-4 w-4 text-gray-400" />
                        )}
                    </button>

                    {showDetails && (
                        <div className="px-4 pb-4">
                            <pre className="overflow-x-auto rounded-lg bg-gray-900 p-3 font-mono text-xs text-gray-300">
                                {normalizedError.traceback.join("")}
                            </pre>
                        </div>
                    )}
                </div>
            )}

            {/* Actions */}
            <div className="flex items-center gap-2 border-t border-gray-200 px-4 py-3">
                {onRetry && (
                    <button
                        onClick={onRetry}
                        className="flex items-center gap-1.5 rounded-md px-3 py-1.5 text-sm font-medium text-blue-600 transition-colors hover:bg-blue-50 hover:text-blue-700"
                    >
                        <RefreshCw className="h-4 w-4" />
                        Retry
                    </button>
                )}
                {isDev && (
                    <button
                        onClick={handleCopy}
                        className="flex items-center gap-1.5 rounded-md px-3 py-1.5 text-sm font-medium text-gray-600 transition-colors hover:bg-gray-100 hover:text-gray-700"
                    >
                        <Copy className="h-4 w-4" />
                        {copied ? "Copied!" : "Copy"}
                    </button>
                )}
            </div>
        </div>
    );
}

/**
 * Inline error display for smaller spaces (e.g., form fields, cards)
 */
export function InlineApiError({
    error,
    className = "",
}: {
    error: string | ApiError | Error;
    className?: string;
}) {
    const message =
        typeof error === "string" ? error : error instanceof Error ? error.message : error.detail;

    return (
        <div className={`flex items-center gap-2 text-sm text-red-600 ${className}`}>
            <AlertCircle className="h-4 w-4 flex-shrink-0" />
            <span>{message}</span>
        </div>
    );
}

export default ApiErrorDisplay;
