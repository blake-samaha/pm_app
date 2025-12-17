"use client";

import { useState } from "react";
import { Project, HealthStatus } from "@/types";
import Link from "next/link";
import { Card, CardContent } from "@/components/ui/card";
import { HealthIndicator } from "@/components/project/HealthIndicator";
import { API_URL } from "@/lib/api";

interface ProjectCardProps {
  project: Project;
}

const statusBorderColors = {
  [HealthStatus.GREEN]: "border-t-green-500",
  [HealthStatus.YELLOW]: "border-t-yellow-500",
  [HealthStatus.RED]: "border-t-red-600",
};

/**
 * Get the full URL for a logo, handling both local uploads and external URLs.
 */
const getLogoUrl = (url: string | undefined | null): string | null => {
  if (!url) return null;
  // If it's a local upload path, prepend the API URL
  if (url.startsWith("/uploads/")) {
    return `${API_URL}${url}`;
  }
  // Otherwise, assume it's an external URL
  return url;
};

export const ProjectCard = ({ project }: ProjectCardProps) => {
  const status = project.health_status_override || project.health_status;
  const [imageError, setImageError] = useState(false);
  
  const logoUrl = getLogoUrl(project.client_logo_url);
  const showLogo = logoUrl && !imageError;

  return (
    <Link href={`/projects/${project.id}`} className="block">
      <Card className={`group relative overflow-hidden transition-all hover:shadow-lg hover:-translate-y-0.5 border-t-4 ${statusBorderColors[status]}`}>
        <CardContent className="p-5">
          <div className="flex items-start justify-between">
            <div className="flex items-center space-x-4">
              {showLogo ? (
                <img
                  src={logoUrl}
                  alt={`${project.name} logo`}
                  className="h-12 w-12 rounded-lg object-cover bg-gray-50"
                  onError={() => setImageError(true)}
                />
              ) : (
                <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-gradient-to-br from-gray-100 to-gray-200 text-xl font-bold text-gray-500">
                  {project.name.charAt(0).toUpperCase()}
                </div>
              )}
              <div>
                <h3 className="text-lg font-semibold text-gray-900 group-hover:text-blue-600">
                  {project.name}
                </h3>
                <p className="text-sm text-gray-500">{project.type}</p>
              </div>
            </div>
            <HealthIndicator 
              status={status} 
              size="sm" 
              variant="solid" 
              label={status}
            />
          </div>
          
          <div className="mt-4 flex items-center justify-between text-sm text-gray-500">
            <span>{project.reporting_cycle ?? "Reporting cycle not provided"}</span>
            <span className={project.is_published ? "text-green-600" : "text-gray-400"}>
              {project.is_published ? "Published" : "Draft"}
            </span>
          </div>
        </CardContent>
      </Card>
    </Link>
  );
};
