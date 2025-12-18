"use client";

import * as React from "react";
import { cn } from "@/lib/utils";

export const Tabs = ({
    children,
    className,
}: {
    children: React.ReactNode;
    className?: string;
}) => <div className={className}>{children}</div>;

export const TabsList = ({
    children,
    className,
}: {
    children: React.ReactNode;
    className?: string;
}) => (
    <div
        className={cn(
            "inline-flex h-10 items-center justify-center rounded-md bg-slate-100 p-1 text-slate-500",
            className
        )}
    >
        {children}
    </div>
);

export const TabsTrigger = ({
    children,
    isActive,
    onClick,
    className,
}: {
    children: React.ReactNode;
    isActive: boolean;
    onClick: () => void;
    className?: string;
}) => (
    <button
        onClick={onClick}
        className={cn(
            "inline-flex items-center justify-center whitespace-nowrap rounded-sm px-3 py-1.5 text-sm font-medium ring-offset-white transition-all focus-visible:outline-none disabled:pointer-events-none disabled:opacity-50",
            isActive
                ? "bg-white text-indigo-600 shadow-sm ring-1 ring-black/5"
                : "text-slate-600 hover:bg-slate-200/50 hover:text-slate-900",
            className
        )}
    >
        {children}
    </button>
);

export const TabsContent = ({
    children,
    isActive,
    className,
}: {
    children: React.ReactNode;
    isActive: boolean;
    className?: string;
}) => {
    if (!isActive) return null;
    return (
        <div className={cn("mt-2 ring-offset-white focus-visible:outline-none", className)}>
            {children}
        </div>
    );
};
