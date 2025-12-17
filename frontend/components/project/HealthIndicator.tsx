import { Project, HealthStatus } from "@/types";
import { AlertTriangle, CheckCircle, AlertCircle } from "lucide-react";

interface HealthIndicatorProps {
  status: HealthStatus;
  label?: string;
  size?: "sm" | "md" | "lg";
}

const statusConfig = {
  [HealthStatus.GREEN]: {
    color: "text-green-700",
    bg: "bg-green-100 border-green-200",
    icon: CheckCircle,
    text: "On Track",
  },
  [HealthStatus.YELLOW]: {
    color: "text-yellow-700",
    bg: "bg-yellow-100 border-yellow-200",
    icon: AlertTriangle,
    text: "Minor Deviation",
  },
  [HealthStatus.RED]: {
    color: "text-red-700",
    bg: "bg-red-100 border-red-200",
    icon: AlertCircle,
    text: "Requires Attention",
  },
};

export const HealthIndicator = ({ status, label, size = "md" }: HealthIndicatorProps) => {
  const config = statusConfig[status];
  const Icon = config.icon;

  const sizeClasses = {
    sm: "h-4 w-4",
    md: "h-5 w-5",
    lg: "h-6 w-6",
  };

  const containerPadding = size === "sm" ? "px-2 py-0.5" : "px-3 py-1.5";

  return (
    <div className={`flex items-center space-x-2 rounded-full border ${config.bg} ${containerPadding}`}>
      <Icon className={`${sizeClasses[size]} ${config.color}`} />
      {label && (
        <span className={`font-semibold ${config.color}`}>
          {label}
        </span>
      )}
    </div>
  );
};

