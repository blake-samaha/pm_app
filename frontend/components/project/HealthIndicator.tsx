import type { HealthStatus } from "@/lib/api/types";
import { HEALTH_STATUS } from "@/lib/domain/enums";
import { AlertTriangle, CheckCircle, AlertCircle, LucideIcon } from "lucide-react";

interface HealthIndicatorProps {
    status: HealthStatus;
    label?: string;
    size?: "sm" | "md" | "lg" | "xl";
    variant?: "subtle" | "solid";
}

interface StatusStyle {
    color: string;
    bg: string;
}

interface StatusConfigEntry {
    subtle: StatusStyle;
    solid: StatusStyle;
    icon: LucideIcon;
    text: string;
}

const statusConfig: Record<HealthStatus, StatusConfigEntry> = {
    [HEALTH_STATUS.GREEN]: {
        subtle: {
            color: "text-green-700",
            bg: "bg-green-100 border-green-200",
        },
        solid: {
            color: "text-white",
            bg: "bg-green-600 border-green-700 shadow-md shadow-green-200",
        },
        icon: CheckCircle,
        text: "On Track",
    },
    [HEALTH_STATUS.YELLOW]: {
        subtle: {
            color: "text-yellow-700",
            bg: "bg-yellow-100 border-yellow-200",
        },
        solid: {
            color: "text-white",
            bg: "bg-yellow-500 border-yellow-600 shadow-md shadow-yellow-200",
        },
        icon: AlertTriangle,
        text: "Minor Deviation",
    },
    [HEALTH_STATUS.RED]: {
        subtle: {
            color: "text-red-700",
            bg: "bg-red-100 border-red-200",
        },
        solid: {
            color: "text-white",
            bg: "bg-red-600 border-red-700 shadow-md shadow-red-200",
        },
        icon: AlertCircle,
        text: "Requires Attention",
    },
};

export const HealthIndicator = ({
    status,
    label,
    size = "md",
    variant = "subtle",
}: HealthIndicatorProps) => {
    const config = statusConfig[status];
    const style = config[variant];
    const Icon = config.icon;

    const sizeClasses = {
        sm: "h-4 w-4",
        md: "h-5 w-5",
        lg: "h-6 w-6",
        xl: "h-8 w-8",
    };

    const containerPadding = {
        sm: "px-2 py-0.5 text-xs",
        md: "px-3 py-1.5 text-sm",
        lg: "px-4 py-2 text-base",
        xl: "px-6 py-3 text-lg",
    };

    return (
        <div
            className={`flex items-center space-x-2 rounded-full border transition-all duration-200 ${style.bg} ${containerPadding[size]}`}
        >
            <Icon className={`${sizeClasses[size]} ${style.color}`} />
            {label && (
                <span className={`font-bold tracking-wide ${style.color}`}>
                    {label.toUpperCase()}
                </span>
            )}
        </div>
    );
};
