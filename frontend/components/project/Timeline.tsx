import { Project } from "@/types";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface TimelineProps {
  project: Project;
}

export const Timeline = ({ project }: TimelineProps) => {
  // Mock timeline data
  const phases = [
    { name: "Discovery", start: 0, duration: 20, color: "bg-blue-500" },
    { name: "Implementation", start: 20, duration: 40, color: "bg-purple-500" },
    { name: "UAT", start: 60, duration: 20, color: "bg-orange-500" },
    { name: "Go Live", start: 80, duration: 10, color: "bg-green-500" },
  ];

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg font-semibold text-gray-900">Timeline</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="relative pt-2">
          {/* Timeline Bar */}
          <div className="flex h-8 w-full overflow-hidden rounded-full bg-gray-100">
            {phases.map((phase, index) => (
              <div
                key={index}
                className={`flex items-center justify-center text-xs font-medium text-white ${phase.color}`}
                style={{ width: `${phase.duration}%` }}
              >
                {phase.duration > 10 && phase.name}
              </div>
            ))}
          </div>

          {/* Legend */}
          <div className="mt-6 flex flex-wrap gap-4">
            {phases.map((phase, index) => (
              <div key={index} className="flex items-center space-x-2">
                <div className={`h-3 w-3 rounded-full ${phase.color}`} />
                <span className="text-sm text-gray-600">{phase.name}</span>
              </div>
            ))}
          </div>
        </div>
      </CardContent>
    </Card>
  );
};
