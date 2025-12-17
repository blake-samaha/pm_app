import { Project, HealthStatus } from "@/types";
import Link from "next/link";
import { Card, CardContent } from "@/components/ui/card";

interface ProjectCardProps {
  project: Project;
}

const statusColors = {
  [HealthStatus.GREEN]: "bg-green-500",
  [HealthStatus.YELLOW]: "bg-yellow-500",
  [HealthStatus.RED]: "bg-red-500",
};

export const ProjectCard = ({ project }: ProjectCardProps) => {
  const status = project.health_status_override || project.health_status;

  return (
    <Link href={`/projects/${project.id}`} className="block">
      <Card className="group relative overflow-hidden transition-all hover:shadow-md">
        <CardContent className="p-6">
          <div className="flex items-start justify-between">
            <div className="flex items-center space-x-4">
              {project.client_logo_url ? (
                <img
                  src={project.client_logo_url}
                  alt={`${project.name} logo`}
                  className="h-12 w-12 rounded-full object-cover"
                />
              ) : (
                <div className="flex h-12 w-12 items-center justify-center rounded-full bg-gray-100 text-xl font-bold text-gray-500">
                  {project.name.charAt(0)}
                </div>
              )}
              <div>
                <h3 className="text-lg font-semibold text-gray-900 group-hover:text-blue-600">
                  {project.name}
                </h3>
                <p className="text-sm text-gray-500">{project.type}</p>
              </div>
            </div>
            <div className={`h-3 w-3 rounded-full ${statusColors[status]}`} />
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
