"use client";

import { useActions } from "@/hooks/useActions";
import { ActionStatus, Priority } from "@/types/actions-risks";
import { Loader2, CheckCircle2, Circle, Clock } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import ApiErrorDisplay from "@/components/ApiErrorDisplay";

interface ActionTableProps {
    projectId: string;
}

const statusIcons = {
    [ActionStatus.TO_DO]: Circle,
    [ActionStatus.IN_PROGRESS]: Clock,
    [ActionStatus.COMPLETE]: CheckCircle2,
};

const statusColors = {
    [ActionStatus.TO_DO]: "text-gray-400",
    [ActionStatus.IN_PROGRESS]: "text-blue-500",
    [ActionStatus.COMPLETE]: "text-green-500",
};

const priorityColors = {
    [Priority.HIGH]: "bg-red-100 text-red-800",
    [Priority.MEDIUM]: "bg-yellow-100 text-yellow-800",
    [Priority.LOW]: "bg-green-100 text-green-800",
};

export const ActionTable = ({ projectId }: ActionTableProps) => {
    const { data: actions, isLoading, isError, error, refetch } = useActions(projectId);

    if (isLoading) {
        return (
            <div className="flex h-32 items-center justify-center">
                <Loader2 className="h-6 w-6 animate-spin text-gray-400" />
            </div>
        );
    }

    if (isError) {
        return (
            <ApiErrorDisplay
                title="Failed to load actions"
                error={(error as any)?.response?.data ?? error ?? "Unknown error"}
                onRetry={() => refetch()}
            />
        );
    }

    if (!actions || actions.length === 0) {
        return (
            <Card>
                <CardContent className="p-8 text-center">
                    <p className="text-gray-500">No action items found.</p>
                </CardContent>
            </Card>
        );
    }

    return (
        <Card className="overflow-hidden">
            <CardHeader className="border-b border-gray-200 bg-gray-50/50 px-6 py-4">
                <CardTitle className="text-lg font-semibold text-gray-900">
                    Action Register
                </CardTitle>
            </CardHeader>
            <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                        <tr>
                            <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                                #
                            </th>
                            <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                                Status
                            </th>
                            <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                                Title
                            </th>
                            <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                                Assignee
                            </th>
                            <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                                Priority
                            </th>
                            <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                                Due Date
                            </th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-200 bg-white">
                        {actions.map((action, index) => {
                            const StatusIcon = statusIcons[action.status];
                            const isPastDue =
                                action.due_date &&
                                new Date(action.due_date) < new Date() &&
                                action.status !== ActionStatus.COMPLETE;

                            return (
                                <tr
                                    key={action.id}
                                    className={`hover:bg-gray-50 ${isPastDue ? "bg-red-50" : ""}`}
                                >
                                    <td className="whitespace-nowrap px-4 py-4 text-sm text-gray-500">
                                        {index + 1}
                                    </td>
                                    <td className="whitespace-nowrap px-6 py-4">
                                        <div className="flex items-center">
                                            <StatusIcon
                                                className={`mr-2 h-5 w-5 ${statusColors[action.status]}`}
                                            />
                                            <span className="text-sm text-gray-900">
                                                {action.status}
                                            </span>
                                        </div>
                                    </td>
                                    <td className="px-6 py-4">
                                        <div className="text-sm font-medium text-gray-900">
                                            {action.title}
                                        </div>
                                        {action.jira_id && (
                                            <div className="text-xs text-gray-500">
                                                Jira: {action.jira_id}
                                            </div>
                                        )}
                                    </td>
                                    <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-500">
                                        {action.assignee || "Unassigned"}
                                    </td>
                                    <td className="whitespace-nowrap px-6 py-4">
                                        <span
                                            className={`inline-flex rounded-full px-2 text-xs font-semibold leading-5 ${priorityColors[action.priority]}`}
                                        >
                                            {action.priority}
                                        </span>
                                    </td>
                                    <td
                                        className={`whitespace-nowrap px-6 py-4 text-sm ${isPastDue ? "font-medium text-red-600" : "text-gray-500"}`}
                                    >
                                        {action.due_date
                                            ? new Date(
                                                  action.due_date
                                              ).toLocaleDateString()
                                            : "-"}
                                    </td>
                                </tr>
                            );
                        })}
                    </tbody>
                </table>
            </div>
        </Card>
    );
};
