"use client";

import React, { Component, ErrorInfo, ReactNode } from "react";
import { AlertTriangle, RefreshCw, Copy, ChevronDown, ChevronUp } from "lucide-react";

interface Props {
    children: ReactNode;
    fallback?: ReactNode;
}

interface State {
    hasError: boolean;
    error: Error | null;
    errorInfo: ErrorInfo | null;
    showDetails: boolean;
    copied: boolean;
}

/**
 * Error Boundary component that catches JavaScript errors in child components.
 * In development mode, shows detailed error information with stack trace.
 * In production, shows a user-friendly error message.
 */
export class ErrorBoundary extends Component<Props, State> {
    constructor(props: Props) {
        super(props);
        this.state = {
            hasError: false,
            error: null,
            errorInfo: null,
            showDetails: false,
            copied: false,
        };
    }

    static getDerivedStateFromError(error: Error): Partial<State> {
        return { hasError: true, error };
    }

    componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
        this.setState({ errorInfo });

        // Log error to console in development
        if (process.env.NODE_ENV === "development") {
            console.error("ErrorBoundary caught an error:", error);
            console.error("Component stack:", errorInfo.componentStack);
        }

        // TODO: Send to error reporting service in production
        // e.g., Sentry, LogRocket, etc.
    }

    handleReset = (): void => {
        this.setState({
            hasError: false,
            error: null,
            errorInfo: null,
            showDetails: false,
        });
    };

    handleCopyError = async (): Promise<void> => {
        const { error, errorInfo } = this.state;
        const errorText = `
Error: ${error?.message}

Stack Trace:
${error?.stack}

Component Stack:
${errorInfo?.componentStack}
        `.trim();

        try {
            await navigator.clipboard.writeText(errorText);
            this.setState({ copied: true });
            setTimeout(() => this.setState({ copied: false }), 2000);
        } catch (err) {
            console.error("Failed to copy error:", err);
        }
    };

    toggleDetails = (): void => {
        this.setState((prev) => ({ showDetails: !prev.showDetails }));
    };

    render(): ReactNode {
        const { hasError, error, errorInfo, showDetails, copied } = this.state;
        const { children, fallback } = this.props;
        const isDev = process.env.NODE_ENV === "development";

        if (hasError) {
            // Use custom fallback if provided
            if (fallback) {
                return fallback;
            }

            return (
                <div className="flex min-h-[400px] items-center justify-center p-6">
                    <div className="w-full max-w-2xl overflow-hidden rounded-xl border border-red-200 bg-white shadow-lg">
                        {/* Header */}
                        <div className="border-b border-red-200 bg-red-50 px-6 py-4">
                            <div className="flex items-center gap-3">
                                <div className="rounded-full bg-red-100 p-2">
                                    <AlertTriangle className="h-6 w-6 text-red-600" />
                                </div>
                                <div>
                                    <h2 className="text-lg font-semibold text-red-900">
                                        Something went wrong
                                    </h2>
                                    <p className="text-sm text-red-700">
                                        {isDev
                                            ? "An error occurred in this component"
                                            : "We're sorry, but something unexpected happened"}
                                    </p>
                                </div>
                            </div>
                        </div>

                        {/* Content */}
                        <div className="space-y-4 p-6">
                            {/* Error message */}
                            {isDev && error && (
                                <div className="overflow-x-auto rounded-lg bg-gray-900 p-4">
                                    <code className="font-mono text-sm text-red-400">
                                        {error.message}
                                    </code>
                                </div>
                            )}

                            {/* Expandable details (dev only) */}
                            {isDev && (
                                <div className="overflow-hidden rounded-lg border border-gray-200">
                                    <button
                                        onClick={this.toggleDetails}
                                        className="flex w-full items-center justify-between bg-gray-50 px-4 py-3 transition-colors hover:bg-gray-100"
                                    >
                                        <span className="text-sm font-medium text-gray-700">
                                            Stack Trace & Details
                                        </span>
                                        {showDetails ? (
                                            <ChevronUp className="h-4 w-4 text-gray-500" />
                                        ) : (
                                            <ChevronDown className="h-4 w-4 text-gray-500" />
                                        )}
                                    </button>

                                    {showDetails && (
                                        <div className="max-h-64 overflow-auto bg-gray-900 p-4">
                                            <pre className="whitespace-pre-wrap font-mono text-xs text-gray-300">
                                                {error?.stack}
                                            </pre>
                                            {errorInfo?.componentStack && (
                                                <>
                                                    <div className="my-3 border-t border-gray-700" />
                                                    <p className="mb-2 text-xs text-gray-500">
                                                        Component Stack:
                                                    </p>
                                                    <pre className="whitespace-pre-wrap font-mono text-xs text-gray-400">
                                                        {errorInfo.componentStack}
                                                    </pre>
                                                </>
                                            )}
                                        </div>
                                    )}
                                </div>
                            )}

                            {/* Actions */}
                            <div className="flex items-center gap-3 pt-2">
                                <button
                                    onClick={this.handleReset}
                                    className="flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-blue-700"
                                >
                                    <RefreshCw className="h-4 w-4" />
                                    Try Again
                                </button>

                                {isDev && (
                                    <button
                                        onClick={this.handleCopyError}
                                        className="flex items-center gap-2 rounded-lg bg-gray-100 px-4 py-2 text-sm font-medium text-gray-700 transition-colors hover:bg-gray-200"
                                    >
                                        <Copy className="h-4 w-4" />
                                        {copied ? "Copied!" : "Copy Error"}
                                    </button>
                                )}

                                <button
                                    onClick={() => window.location.reload()}
                                    className="px-4 py-2 text-sm font-medium text-gray-600 hover:text-gray-900"
                                >
                                    Reload Page
                                </button>
                            </div>

                            {/* Help text */}
                            {!isDev && (
                                <p className="text-sm text-gray-500">
                                    If this problem persists, please contact support.
                                </p>
                            )}
                        </div>
                    </div>
                </div>
            );
        }

        return children;
    }
}

/**
 * Hook-friendly wrapper for using ErrorBoundary with function components.
 * Use this to wrap specific sections of your app that might fail.
 */
export function withErrorBoundary<P extends object>(
    WrappedComponent: React.ComponentType<P>,
    fallback?: ReactNode
): React.FC<P> {
    return function WithErrorBoundary(props: P) {
        return (
            <ErrorBoundary fallback={fallback}>
                <WrappedComponent {...props} />
            </ErrorBoundary>
        );
    };
}

export default ErrorBoundary;
