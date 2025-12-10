import { Project, HealthStatus } from "@/types";
import { AlertTriangle, CheckCircle, AlertCircle } from "lucide-react";

interface HealthIndicatorProps {
  status: HealthStatus;
  label?: string;
  size?: "sm" | "md" | "lg";
}

const statusConfig = {
  [HealthStatus.GREEN]: {
    color: "text-green-500",
    bg: "bg-green-100",
    icon: CheckCircle,
    text: "On Track",
  },
  [HealthStatus.YELLOW]: {
    color: "text-yellow-500",
    bg: "bg-yellow-100",
    icon: AlertTriangle,
    text: "Minor Deviation",
  },
  [HealthStatus.RED]: {
    color: "text-red-500",
    bg: "bg-red-100",
    icon: AlertCircle,
    text: "Requires Attention",
  },
};

export const HealthIndicator = ({ status, label, size = "md" }: HealthIndicatorProps) => {
  const config = statusConfig[status];
  const Icon = config.icon;

  const sizeClasses = {
    sm: "h-4 w-4",
    md: "h-6 w-6",
    lg: "h-8 w-8",
  };

  return (
    <div className="flex items-center space-x-2">
      <Icon className={`${sizeClasses[size]} ${config.color}`} />
      {label && (
        <span className={`font-medium ${config.color}`}>
          {label}
        </span>
      )}
    </div>
  );
};

