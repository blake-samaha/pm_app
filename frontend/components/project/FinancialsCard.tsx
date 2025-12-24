import type { Project, UserRole } from "@/lib/api/types";
import { ProjectType } from "@/lib/api/types";
import { PROJECT_TYPE } from "@/lib/domain/enums";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import ApiErrorDisplay from "@/components/ApiErrorDisplay";
import { FinancialsChart } from "./FinancialsChart";
import { useEffectiveUser } from "@/hooks/useEffectiveUser";
import { canViewFinancials } from "@/lib/permissions";

interface FinancialsCardProps {
    project: Project;
}

export const FinancialsCard = ({ project }: FinancialsCardProps) => {
    const user = useEffectiveUser();

    // Gate visibility by role - only Cogniters and Client+Financials can view
    if (!user || !canViewFinancials(user.role as UserRole)) {
        return null;
    }

    if (project.type === PROJECT_TYPE.RETAINER) {
        return null;
    }

    const hasAnyData =
        project.total_budget !== undefined ||
        project.remaining_budget !== undefined ||
        project.overrun_investment !== undefined ||
        project.total_days_actuals !== undefined;

    const currency = project.currency || "USD";
    const formatter = new Intl.NumberFormat("en-US", {
        style: "currency",
        currency: currency,
        maximumFractionDigits: 0,
    });

    // Format large numbers with 1 decimal (e.g., 263.5)
    const numberFormatter = new Intl.NumberFormat("en-US", {
        maximumFractionDigits: 1,
    });

    return (
        <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-lg font-semibold text-slate-900">Financials</CardTitle>
                <span className="rounded-full bg-slate-100 px-2 py-1 text-xs font-medium text-slate-600">
                    {project.type}
                </span>
            </CardHeader>
            <CardContent className="pt-4">
                {hasAnyData ? (
                    <div className="space-y-6">
                        {project.total_budget ? (
                            <FinancialsChart
                                total={project.total_budget}
                                spent={project.spent_budget || 0}
                                remaining={project.remaining_budget || 0}
                                currency={currency}
                            />
                        ) : (
                            <div className="rounded-lg border border-dashed border-slate-200 bg-slate-50 p-4 text-center">
                                <p className="text-sm text-slate-500">
                                    Total budget calculation unavailable (Missing Day Price or FTE
                                    Days in Salesforce)
                                </p>
                            </div>
                        )}

                        {/* Metrics Grid */}
                        <div className="grid grid-cols-3 gap-4 border-t border-slate-100 pt-6 text-center">
                            <div>
                                <p className="text-[10px] font-bold uppercase tracking-widest text-slate-400">
                                    Total
                                </p>
                                <p className="mt-1 text-lg font-bold text-slate-900">
                                    {project.total_budget
                                        ? formatter.format(project.total_budget)
                                        : "--"}
                                </p>
                            </div>
                            <div>
                                <p className="text-[10px] font-bold uppercase tracking-widest text-slate-400">
                                    Spent
                                </p>
                                <p className="mt-1 text-lg font-bold text-slate-900">
                                    {project.spent_budget
                                        ? formatter.format(project.spent_budget)
                                        : "--"}
                                </p>
                            </div>
                            <div>
                                <p className="text-[10px] font-bold uppercase tracking-widest text-slate-400">
                                    Remaining
                                </p>
                                <p
                                    className={`mt-1 text-lg font-bold ${
                                        (project.remaining_budget || 0) < 0
                                            ? "text-red-600"
                                            : "text-emerald-600"
                                    }`}
                                >
                                    {project.remaining_budget
                                        ? formatter.format(project.remaining_budget)
                                        : "--"}
                                </p>
                            </div>
                        </div>

                        {/* Additional Details Table */}
                        <div className="border-t border-slate-100 pt-6">
                            <h4 className="mb-3 text-sm font-semibold text-slate-900">
                                Detailed Metrics
                            </h4>
                            <div className="rounded-md border border-slate-100">
                                <table className="w-full text-sm">
                                    <tbody>
                                        <tr className="border-b border-slate-50">
                                            <td className="px-4 py-2 text-slate-500">
                                                Overrun Investment
                                            </td>
                                            <td className="px-4 py-2 text-right font-medium text-slate-900">
                                                {project.overrun_investment
                                                    ? formatter.format(project.overrun_investment)
                                                    : "--"}
                                            </td>
                                        </tr>
                                        <tr className="border-b border-slate-50">
                                            <td className="px-4 py-2 text-slate-500">
                                                Total Actual Days
                                            </td>
                                            <td className="px-4 py-2 text-right font-medium text-slate-900">
                                                {project.total_days_actuals
                                                    ? numberFormatter.format(
                                                          project.total_days_actuals
                                                      )
                                                    : "--"}
                                            </td>
                                        </tr>
                                        <tr className="border-b border-slate-50">
                                            <td className="px-4 py-2 text-slate-500">
                                                Budgeted Days (Delivery)
                                            </td>
                                            <td className="px-4 py-2 text-right font-medium text-slate-900">
                                                {project.budgeted_days_delivery
                                                    ? numberFormatter.format(
                                                          project.budgeted_days_delivery
                                                      )
                                                    : "--"}
                                            </td>
                                        </tr>
                                        <tr>
                                            <td className="px-4 py-2 text-slate-500">
                                                Budgeted Hours (Delivery)
                                            </td>
                                            <td className="px-4 py-2 text-right font-medium text-slate-900">
                                                {project.budgeted_hours_delivery
                                                    ? numberFormatter.format(
                                                          project.budgeted_hours_delivery
                                                      )
                                                    : "--"}
                                            </td>
                                        </tr>
                                    </tbody>
                                </table>
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
