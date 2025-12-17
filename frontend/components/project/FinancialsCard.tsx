import { Project, ProjectType } from "@/types";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import ApiErrorDisplay from "@/components/ApiErrorDisplay";
import { FinancialsChart } from "./FinancialsChart";

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

    return (
        <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-lg font-semibold text-slate-900">
                    Financials
                </CardTitle>
                <span className="rounded-full bg-slate-100 px-2 py-1 text-xs font-medium text-slate-600">
                    {project.type}
                </span>
            </CardHeader>
            <CardContent className="pt-4">
                {hasFinancials ? (
                    <div className="space-y-6">
                        <FinancialsChart 
                            total={project.total_budget!}
                            spent={project.spent_budget || 0}
                            remaining={project.remaining_budget || 0}
                            currency={currency}
                        />

                        {/* Metrics Grid */}
                        <div className="grid grid-cols-3 gap-4 border-t border-slate-100 pt-6">
                            <div>
                                <p className="text-xs font-medium text-slate-500 uppercase tracking-wider">
                                    Total
                                </p>
                                <p className="mt-1 text-sm font-semibold text-slate-900">
                                    {formatter.format(project.total_budget!)}
                                </p>
                            </div>
                            <div>
                                <p className="text-xs font-medium text-slate-500 uppercase tracking-wider">
                                    Spent
                                </p>
                                <p className="mt-1 text-sm font-semibold text-slate-900">
                                    {formatter.format(project.spent_budget || 0)}
                                </p>
                            </div>
                            <div>
                                <p className="text-xs font-medium text-slate-500 uppercase tracking-wider">
                                    Remaining
                                </p>
                                <p className={`mt-1 text-sm font-semibold ${
                                    (project.remaining_budget || 0) < 0 ? "text-red-600" : "text-emerald-600"
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
