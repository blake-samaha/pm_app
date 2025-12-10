import { Project, ProjectType } from "@/types";
import { DollarSign, TrendingUp } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface FinancialsCardProps {
  project: Project;
}

export const FinancialsCard = ({ project }: FinancialsCardProps) => {
  // Mock data for now - eventually this comes from Precursive
  const budget = 500000;
  const spent = 175000;
  const remaining = budget - spent;
  const percentSpent = (spent / budget) * 100;

  if (project.type === ProjectType.SAAS_REVENUE) {
    return null; // Or show ARR
  }

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-lg font-semibold text-gray-900">Financials</CardTitle>
        <span className="rounded-full bg-gray-100 px-2 py-1 text-xs font-medium text-gray-600">
          {project.type}
        </span>
      </CardHeader>
      <CardContent className="space-y-6 pt-4">
        <div>
          <div className="flex justify-between text-sm font-medium text-gray-500">
            <span>Budget Consumed</span>
            <span>{percentSpent.toFixed(1)}%</span>
          </div>
          <div className="mt-2 h-2 w-full overflow-hidden rounded-full bg-gray-100">
            <div
              className="h-full bg-blue-600 transition-all duration-500"
              style={{ width: `${percentSpent}%` }}
            />
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div className="rounded-lg bg-gray-50 p-3">
            <div className="flex items-center space-x-2 text-sm text-gray-500">
              <DollarSign className="h-4 w-4" />
              <span>Total Budget</span>
            </div>
            <p className="mt-1 text-lg font-bold text-gray-900">
              ${budget.toLocaleString()}
            </p>
          </div>
          <div className="rounded-lg bg-gray-50 p-3">
            <div className="flex items-center space-x-2 text-sm text-gray-500">
              <TrendingUp className="h-4 w-4" />
              <span>Remaining</span>
            </div>
            <p className="mt-1 text-lg font-bold text-green-600">
              ${remaining.toLocaleString()}
            </p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};
