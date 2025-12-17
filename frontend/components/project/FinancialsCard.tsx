import { Project, ProjectType } from "@/types";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import ApiErrorDisplay from "@/components/ApiErrorDisplay";

interface FinancialsCardProps {
    project: Project;
}

export const FinancialsCard = ({ project }: FinancialsCardProps) => {
    if (project.type === ProjectType.RETAINER) {
        return null;
    }

    const hasFinancials = project.total_budget !== undefined && project.total_budget > 0;
    const currency = project.currency || "USD";
    const formatter = new Intl.NumberFormat("en-US", {
        style: "currency",
        currency: currency,
        maximumFractionDigits: 0,
    });

    const percentSpent =
        project.total_budget && project.spent_budget
            ? Math.min((project.spent_budget / project.total_budget) * 100, 100)
            : 0;

    return (
        <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-lg font-semibold text-gray-900">
                    Financials
                </CardTitle>
                <span className="rounded-full bg-gray-100 px-2 py-1 text-xs font-medium text-gray-600">
                    {project.type}
                </span>
            </CardHeader>
            <CardContent className="pt-4">
                {hasFinancials ? (
                    <div className="space-y-6">
                        {/* Progress Bar */}
                        <div className="space-y-2">
                            <div className="flex justify-between text-sm">
                                <span className="font-medium text-gray-700">Budget Used</span>
                                <span className="text-gray-500">
                                    {Math.round(percentSpent)}%
                                </span>
                            </div>
                            <div className="h-2 w-full overflow-hidden rounded-full bg-gray-100">
                                <div
                                    className={`h-full rounded-full transition-all duration-500 ${
                                        percentSpent > 90
                                            ? "bg-red-500"
                                            : percentSpent > 75
                                            ? "bg-yellow-500"
                                            : "bg-green-500"
                                    }`}
                                    style={{ width: `${percentSpent}%` }}
                                />
                            </div>
                        </div>

                        {/* Metrics Grid */}
                        <div className="grid grid-cols-3 gap-4 border-t border-gray-100 pt-4">
                            <div>
                                <p className="text-xs font-medium text-gray-500 uppercase tracking-wider">
                                    Total
                                </p>
                                <p className="mt-1 text-sm font-semibold text-gray-900">
                                    {formatter.format(project.total_budget!)}
                                </p>
                            </div>
                            <div>
                                <p className="text-xs font-medium text-gray-500 uppercase tracking-wider">
                                    Spent
                                </p>
                                <p className="mt-1 text-sm font-semibold text-gray-900">
                                    {formatter.format(project.spent_budget || 0)}
                                </p>
                            </div>
                            <div>
                                <p className="text-xs font-medium text-gray-500 uppercase tracking-wider">
                                    Remaining
                                </p>
                                <p className={`mt-1 text-sm font-semibold ${
                                    (project.remaining_budget || 0) < 0 ? "text-red-600" : "text-green-600"
                                }`}>
                                    {formatter.format(project.remaining_budget || 0)}
                                </p>
                            </div>
                        </div>
                    </div>
                ) : (
                    <ApiErrorDisplay
                        title="Financial data unavailable"
                        error="Sync data to view project financials."
                    />
                )}
            </CardContent>
        </Card>
    );
};
