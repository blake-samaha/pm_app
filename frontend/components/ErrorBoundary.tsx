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
                <div className="min-h-[400px] flex items-center justify-center p-6">
                    <div className="max-w-2xl w-full bg-white rounded-xl shadow-lg border border-red-200 overflow-hidden">
                        {/* Header */}
                        <div className="bg-red-50 px-6 py-4 border-b border-red-200">
                            <div className="flex items-center gap-3">
                                <div className="p-2 bg-red-100 rounded-full">
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
                        <div className="p-6 space-y-4">
                            {/* Error message */}
                            {isDev && error && (
                                <div className="bg-gray-900 rounded-lg p-4 overflow-x-auto">
                                    <code className="text-red-400 text-sm font-mono">
                                        {error.message}
                                    </code>
                                </div>
                            )}

                            {/* Expandable details (dev only) */}
                            {isDev && (
                                <div className="border border-gray-200 rounded-lg overflow-hidden">
                                    <button
                                        onClick={this.toggleDetails}
                                        className="w-full flex items-center justify-between px-4 py-3 bg-gray-50 hover:bg-gray-100 transition-colors"
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
                                        <div className="p-4 bg-gray-900 max-h-64 overflow-auto">
                                            <pre className="text-xs text-gray-300 font-mono whitespace-pre-wrap">
                                                {error?.stack}
                                            </pre>
                                            {errorInfo?.componentStack && (
                                                <>
                                                    <div className="my-3 border-t border-gray-700" />
                                                    <p className="text-xs text-gray-500 mb-2">
                                                        Component Stack:
                                                    </p>
                                                    <pre className="text-xs text-gray-400 font-mono whitespace-pre-wrap">
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
                                    className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium"
                                >
                                    <RefreshCw className="h-4 w-4" />
                                    Try Again
                                </button>

                                {isDev && (
                                    <button
                                        onClick={this.handleCopyError}
                                        className="flex items-center gap-2 px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors text-sm font-medium"
                                    >
                                        <Copy className="h-4 w-4" />
                                        {copied ? "Copied!" : "Copy Error"}
                                    </button>
                                )}

                                <button
                                    onClick={() => window.location.reload()}
                                    className="px-4 py-2 text-gray-600 hover:text-gray-900 text-sm font-medium"
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

