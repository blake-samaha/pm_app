"use client";

import { useActions } from "@/hooks/useActions";
import { ActionItem, ActionStatus, Priority } from "@/types/actions-risks";
import {
    Loader2,
    CheckCircle2,
    Circle,
    Clock,
    Filter,
    X,
    Search,
    ExternalLink,
    ChevronLeft,
    ChevronRight,
    HelpCircle,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardFooter } from "@/components/ui/card";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { Checkbox } from "@/components/ui/checkbox";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import ApiErrorDisplay from "@/components/ApiErrorDisplay";
import { useState, useMemo } from "react";
import { useProject } from "@/hooks/useProjects"; // Import useProject to get Jira URL context

interface ActionTableProps {
    projectId: string;
}

const ITEMS_PER_PAGE = 25;

const statusIcons = {
    [ActionStatus.TO_DO]: Circle,
    [ActionStatus.IN_PROGRESS]: Clock,
    [ActionStatus.COMPLETE]: CheckCircle2,
    [ActionStatus.NO_STATUS]: HelpCircle,
};

const statusColors = {
    [ActionStatus.TO_DO]: "text-slate-400",
    [ActionStatus.IN_PROGRESS]: "text-blue-500",
    [ActionStatus.COMPLETE]: "text-emerald-500",
    [ActionStatus.NO_STATUS]: "text-slate-300",
};

const priorityColors = {
    [Priority.HIGH]: "bg-red-100 text-red-800",
    [Priority.MEDIUM]: "bg-amber-100 text-amber-800",
    [Priority.LOW]: "bg-emerald-100 text-emerald-800",
};

type DueDateFilter = "overdue" | "due_today" | "due_this_week" | "due_this_month" | "no_due_date";

type FilterState = {
    statuses: ActionStatus[];
    priorities: Priority[];
    assignees: string[];
    dueDates: DueDateFilter[];
    search: string;
};

export const ActionTable = ({ projectId }: ActionTableProps) => {
    const { data: actions, isLoading, isError, error, refetch } = useActions(projectId);
    const { data: project } = useProject(projectId); // Fetch project to construct Jira URLs

    // Filter States
    const [filters, setFilters] = useState<FilterState>({
        statuses: [],
        priorities: [],
        assignees: [],
        dueDates: [],
        search: "",
    });

    // Pagination State
    const [currentPage, setCurrentPage] = useState(1);

    // Helper to construct Jira Issue URL
    const getJiraIssueUrl = (jiraId: string) => {
        // Fallback if project.jira_url isn't set but we have an ID (e.g. assume cloud hostname if we could, but better to just require the URL)
        if (!project?.jira_url || !jiraId) return null;

        // Ensure no trailing slash on base URL
        const baseUrl = project.jira_url.replace(/\/$/, "");
        return `${baseUrl}/browse/${jiraId}`;
    };

    // Derived unique lists for filter options
    const uniqueAssignees = useMemo(() => {
        if (!actions) return [];
        const assignees = actions.map((a) => a.assignee).filter((a): a is string => !!a); // Filter out null/undefined
        return Array.from(new Set(assignees)).sort();
    }, [actions]);

    const filteredActions = useMemo(() => {
        // Reset to first page when filters change
        if (currentPage !== 1) {
            setCurrentPage(1);
        }

        if (!actions) return [];

        const now = new Date();
        const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
        const endOfWeek = new Date(today);
        endOfWeek.setDate(today.getDate() + (7 - today.getDay())); // End of current week (Sunday)
        const endOfMonth = new Date(now.getFullYear(), now.getMonth() + 1, 0); // Last day of current month

        return actions.filter((action) => {
            const matchesSearch =
                action.title.toLowerCase().includes(filters.search.toLowerCase()) ||
                (action.jira_id &&
                    action.jira_id.toLowerCase().includes(filters.search.toLowerCase()));

            const matchesStatus =
                filters.statuses.length === 0 || filters.statuses.includes(action.status);
            const matchesPriority =
                filters.priorities.length === 0 || filters.priorities.includes(action.priority);

            // Handle "Unassigned" case specially if we want to, but here checking exact match
            const matchesAssignee =
                filters.assignees.length === 0 ||
                (action.assignee && filters.assignees.includes(action.assignee));

            // Due date filtering
            const matchesDueDate =
                filters.dueDates.length === 0 ||
                (() => {
                    if (!action.due_date) {
                        return filters.dueDates.includes("no_due_date");
                    }

                    const dueDate = new Date(action.due_date);
                    const isOverdue = dueDate < today && action.status !== ActionStatus.COMPLETE;
                    const isDueToday = dueDate.getTime() === today.getTime();
                    const isDueThisWeek = dueDate >= today && dueDate <= endOfWeek;
                    const isDueThisMonth = dueDate >= today && dueDate <= endOfMonth;

                    return filters.dueDates.some((filter) => {
                        if (filter === "overdue") return isOverdue;
                        if (filter === "due_today") return isDueToday;
                        if (filter === "due_this_week") return isDueThisWeek;
                        if (filter === "due_this_month") return isDueThisMonth;
                        return false;
                    });
                })();

            return (
                matchesSearch &&
                matchesStatus &&
                matchesPriority &&
                matchesAssignee &&
                matchesDueDate
            );
        });
    }, [actions, filters]);

    // Pagination Logic
    const totalPages = Math.ceil(filteredActions.length / ITEMS_PER_PAGE);
    const paginatedActions = useMemo(() => {
        const startIndex = (currentPage - 1) * ITEMS_PER_PAGE;
        return filteredActions.slice(startIndex, startIndex + ITEMS_PER_PAGE);
    }, [filteredActions, currentPage]);

    const toggleFilter = (type: keyof FilterState, value: string) => {
        setFilters((prev) => {
            const current = prev[type] as string[];
            const updated = current.includes(value)
                ? current.filter((item) => item !== value)
                : [...current, value];
            return { ...prev, [type]: updated };
        });
    };

    const clearFilters = () => {
        setFilters({
            statuses: [],
            priorities: [],
            assignees: [],
            dueDates: [],
            search: "",
        });
    };

    const hasFilters =
        filters.statuses.length > 0 ||
        filters.priorities.length > 0 ||
        filters.assignees.length > 0 ||
        filters.dueDates.length > 0 ||
        filters.search;

    if (isLoading) {
        return (
            <Card className="flex h-96 items-center justify-center">
                <Loader2 className="h-8 w-8 animate-spin text-slate-400" />
            </Card>
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

    return (
        <Card className="overflow-hidden border-slate-200 shadow-sm">
            <CardHeader className="border-b border-slate-100 bg-white px-6 py-5">
                <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
                    <div className="flex items-center space-x-4">
                        <CardTitle className="text-lg font-semibold text-slate-900">
                            Action Register
                        </CardTitle>
                        {hasFilters && (
                            <button
                                onClick={clearFilters}
                                className="flex items-center rounded-md border border-slate-200 bg-slate-50 px-2 py-1 text-xs font-medium text-slate-500 transition-colors hover:text-red-600"
                            >
                                <X className="mr-1 h-3 w-3" />
                                Clear {filteredActions.length !== actions?.length ? "Filters" : ""}
                            </button>
                        )}
                    </div>

                    <div className="flex items-center gap-3">
                        {/* Top Pagination Controls */}
                        {totalPages > 1 && (
                            <div className="mr-2 flex items-center space-x-1 rounded-md border border-slate-100 bg-slate-50 p-0.5">
                                <Button
                                    variant="ghost"
                                    size="sm"
                                    onClick={() => setCurrentPage((prev) => Math.max(prev - 1, 1))}
                                    disabled={currentPage === 1}
                                    className="h-7 w-7 p-0 hover:bg-white hover:shadow-sm"
                                >
                                    <ChevronLeft className="h-3.5 w-3.5 text-slate-600" />
                                </Button>
                                <span className="min-w-[3rem] px-2 text-center text-[10px] font-semibold text-slate-600">
                                    {currentPage} / {totalPages}
                                </span>
                                <Button
                                    variant="ghost"
                                    size="sm"
                                    onClick={() =>
                                        setCurrentPage((prev) => Math.min(prev + 1, totalPages))
                                    }
                                    disabled={currentPage === totalPages}
                                    className="h-7 w-7 p-0 hover:bg-white hover:shadow-sm"
                                >
                                    <ChevronRight className="h-3.5 w-3.5 text-slate-600" />
                                </Button>
                            </div>
                        )}

                        {/* Search */}
                        <div className="relative">
                            <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-slate-400" />
                            <Input
                                placeholder="Search..."
                                value={filters.search}
                                onChange={(e) =>
                                    setFilters((prev) => ({ ...prev, search: e.target.value }))
                                }
                                className="w-[200px] pl-9"
                            />
                        </div>
                    </div>
                </div>
            </CardHeader>

            <div className="min-h-[400px] overflow-x-visible">
                <table className="min-w-full divide-y divide-slate-100">
                    <thead className="bg-slate-50/50">
                        <tr>
                            {/* Row Number Column */}
                            <th className="w-12 px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-slate-500">
                                #
                            </th>
                            {/* Status Filter */}
                            <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-slate-500">
                                <div className="flex items-center space-x-2">
                                    <span>Status</span>
                                    <Popover>
                                        <PopoverTrigger asChild>
                                            <button
                                                className={`rounded-md p-1 transition-colors hover:bg-slate-200 ${filters.statuses.length > 0 ? "bg-blue-50 text-blue-600" : ""}`}
                                            >
                                                <Filter className="h-3 w-3" />
                                            </button>
                                        </PopoverTrigger>
                                        <PopoverContent className="w-48 p-3" align="start">
                                            <div className="space-y-2">
                                                <h4 className="mb-2 text-xs font-medium uppercase text-slate-500">
                                                    Filter by Status
                                                </h4>
                                                {Object.values(ActionStatus).map((status) => (
                                                    <div
                                                        key={status}
                                                        className="flex items-center space-x-2"
                                                    >
                                                        <Checkbox
                                                            id={`status-${status}`}
                                                            checked={filters.statuses.includes(
                                                                status
                                                            )}
                                                            onCheckedChange={() =>
                                                                toggleFilter("statuses", status)
                                                            }
                                                        />
                                                        <label
                                                            htmlFor={`status-${status}`}
                                                            className="cursor-pointer select-none text-sm text-slate-700"
                                                        >
                                                            {status}
                                                        </label>
                                                    </div>
                                                ))}
                                            </div>
                                        </PopoverContent>
                                    </Popover>
                                </div>
                            </th>

                            <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-slate-500">
                                Title
                            </th>

                            {/* Assignee Filter */}
                            <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-slate-500">
                                <div className="flex items-center space-x-2">
                                    <span>Assignee</span>
                                    <Popover>
                                        <PopoverTrigger asChild>
                                            <button
                                                className={`rounded-md p-1 transition-colors hover:bg-slate-200 ${filters.assignees.length > 0 ? "bg-blue-50 text-blue-600" : ""}`}
                                            >
                                                <Filter className="h-3 w-3" />
                                            </button>
                                        </PopoverTrigger>
                                        <PopoverContent className="w-56 p-3" align="start">
                                            <div className="space-y-2">
                                                <h4 className="mb-2 text-xs font-medium uppercase text-slate-500">
                                                    Filter by Assignee
                                                </h4>
                                                {uniqueAssignees.length > 0 ? (
                                                    <div className="max-h-48 space-y-2 overflow-y-auto">
                                                        {uniqueAssignees.map((assignee) => (
                                                            <div
                                                                key={assignee}
                                                                className="flex items-center space-x-2"
                                                            >
                                                                <Checkbox
                                                                    id={`assignee-${assignee}`}
                                                                    checked={filters.assignees.includes(
                                                                        assignee
                                                                    )}
                                                                    onCheckedChange={() =>
                                                                        toggleFilter(
                                                                            "assignees",
                                                                            assignee
                                                                        )
                                                                    }
                                                                />
                                                                <label
                                                                    htmlFor={`assignee-${assignee}`}
                                                                    className="cursor-pointer select-none truncate text-sm text-slate-700"
                                                                >
                                                                    {assignee}
                                                                </label>
                                                            </div>
                                                        ))}
                                                    </div>
                                                ) : (
                                                    <p className="text-xs italic text-slate-400">
                                                        No assignees found
                                                    </p>
                                                )}
                                            </div>
                                        </PopoverContent>
                                    </Popover>
                                </div>
                            </th>

                            {/* Priority Filter */}
                            <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-slate-500">
                                <div className="flex items-center space-x-2">
                                    <span>Priority</span>
                                    <Popover>
                                        <PopoverTrigger asChild>
                                            <button
                                                className={`rounded-md p-1 transition-colors hover:bg-slate-200 ${filters.priorities.length > 0 ? "bg-blue-50 text-blue-600" : ""}`}
                                            >
                                                <Filter className="h-3 w-3" />
                                            </button>
                                        </PopoverTrigger>
                                        <PopoverContent className="w-48 p-3" align="start">
                                            <div className="space-y-2">
                                                <h4 className="mb-2 text-xs font-medium uppercase text-slate-500">
                                                    Filter by Priority
                                                </h4>
                                                {Object.values(Priority).map((priority) => (
                                                    <div
                                                        key={priority}
                                                        className="flex items-center space-x-2"
                                                    >
                                                        <Checkbox
                                                            id={`priority-${priority}`}
                                                            checked={filters.priorities.includes(
                                                                priority
                                                            )}
                                                            onCheckedChange={() =>
                                                                toggleFilter("priorities", priority)
                                                            }
                                                        />
                                                        <label
                                                            htmlFor={`priority-${priority}`}
                                                            className="cursor-pointer select-none text-sm text-slate-700"
                                                        >
                                                            {priority}
                                                        </label>
                                                    </div>
                                                ))}
                                            </div>
                                        </PopoverContent>
                                    </Popover>
                                </div>
                            </th>

                            {/* Due Date Filter */}
                            <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-slate-500">
                                <div className="flex items-center space-x-2">
                                    <span>Due Date</span>
                                    <Popover>
                                        <PopoverTrigger asChild>
                                            <button
                                                className={`rounded-md p-1 transition-colors hover:bg-slate-200 ${filters.dueDates.length > 0 ? "bg-blue-50 text-blue-600" : ""}`}
                                            >
                                                <Filter className="h-3 w-3" />
                                            </button>
                                        </PopoverTrigger>
                                        <PopoverContent className="w-56 p-3" align="start">
                                            <div className="space-y-2">
                                                <h4 className="mb-2 text-xs font-medium uppercase text-slate-500">
                                                    Filter by Due Date
                                                </h4>
                                                {[
                                                    { value: "overdue", label: "Overdue" },
                                                    { value: "due_today", label: "Due Today" },
                                                    {
                                                        value: "due_this_week",
                                                        label: "Due This Week",
                                                    },
                                                    {
                                                        value: "due_this_month",
                                                        label: "Due This Month",
                                                    },
                                                    { value: "no_due_date", label: "No Due Date" },
                                                ].map((option) => (
                                                    <div
                                                        key={option.value}
                                                        className="flex items-center space-x-2"
                                                    >
                                                        <Checkbox
                                                            id={`dueDate-${option.value}`}
                                                            checked={filters.dueDates.includes(
                                                                option.value as DueDateFilter
                                                            )}
                                                            onCheckedChange={() =>
                                                                toggleFilter(
                                                                    "dueDates",
                                                                    option.value
                                                                )
                                                            }
                                                        />
                                                        <label
                                                            htmlFor={`dueDate-${option.value}`}
                                                            className="cursor-pointer select-none text-sm text-slate-700"
                                                        >
                                                            {option.label}
                                                        </label>
                                                    </div>
                                                ))}
                                            </div>
                                        </PopoverContent>
                                    </Popover>
                                </div>
                            </th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100 bg-white">
                        {paginatedActions.length > 0 ? (
                            paginatedActions.map((action, index) => {
                                const StatusIcon = statusIcons[action.status];
                                const isPastDue =
                                    action.due_date &&
                                    new Date(action.due_date) < new Date() &&
                                    action.status !== ActionStatus.COMPLETE;

                                const jiraUrl = getJiraIssueUrl(action.jira_id || "");
                                const absoluteIndex =
                                    (currentPage - 1) * ITEMS_PER_PAGE + index + 1;

                                return (
                                    <tr
                                        key={action.id}
                                        className={`group transition-colors hover:bg-slate-50/50`}
                                    >
                                        {/* Row Number */}
                                        <td className="whitespace-nowrap px-4 py-2.5 text-sm font-medium text-slate-400">
                                            {absoluteIndex}
                                        </td>
                                        <td className="whitespace-nowrap px-6 py-2.5">
                                            <div
                                                className="flex items-center"
                                                title={action.status}
                                            >
                                                <StatusIcon
                                                    className={`h-5 w-5 ${statusColors[action.status]}`}
                                                />
                                            </div>
                                        </td>
                                        <td className="px-6 py-2.5">
                                            {jiraUrl ? (
                                                <a
                                                    href={jiraUrl}
                                                    target="_blank"
                                                    rel="noopener noreferrer"
                                                    className="group/link flex cursor-pointer items-start"
                                                >
                                                    <span className="mr-1 text-sm font-medium text-blue-600 transition-all hover:text-blue-700 hover:underline">
                                                        {action.title}
                                                    </span>
                                                    <ExternalLink className="mt-1 h-3 w-3 flex-shrink-0 text-blue-500 opacity-70 transition-opacity group-hover/link:opacity-100" />
                                                </a>
                                            ) : (
                                                <div className="text-sm font-medium text-slate-900">
                                                    {action.title}
                                                </div>
                                            )}

                                            {action.jira_id && (
                                                <div className="mt-0.5 flex items-center">
                                                    <span className="inline-flex items-center rounded border border-slate-200 bg-slate-50 px-1.5 py-0.5 text-[10px] font-medium text-slate-500">
                                                        {action.jira_id}
                                                    </span>
                                                </div>
                                            )}
                                        </td>
                                        <td className="whitespace-nowrap px-6 py-2.5 text-sm text-slate-600">
                                            {action.assignee ? (
                                                <div className="flex items-center">
                                                    <div className="mr-2 flex h-6 w-6 items-center justify-center rounded-full border border-slate-200 bg-slate-100 text-xs font-medium text-slate-600">
                                                        {action.assignee.charAt(0).toUpperCase()}
                                                    </div>
                                                    {action.assignee}
                                                </div>
                                            ) : (
                                                <span className="italic text-slate-400">
                                                    Unassigned
                                                </span>
                                            )}
                                        </td>
                                        <td className="whitespace-nowrap px-6 py-2.5">
                                            <span
                                                className={`inline-flex rounded-full px-2.5 py-0.5 text-xs font-medium ${priorityColors[action.priority]}`}
                                            >
                                                {action.priority}
                                            </span>
                                        </td>
                                        <td className="whitespace-nowrap px-6 py-2.5 text-sm">
                                            {action.due_date ? (
                                                <span
                                                    className={
                                                        isPastDue
                                                            ? "font-medium text-red-600"
                                                            : "text-slate-500"
                                                    }
                                                >
                                                    {new Date(action.due_date).toLocaleDateString()}
                                                </span>
                                            ) : (
                                                <span className="text-slate-400">-</span>
                                            )}
                                        </td>
                                    </tr>
                                );
                            })
                        ) : (
                            <tr>
                                <td colSpan={6} className="px-6 py-12 text-center text-slate-500">
                                    <div className="flex flex-col items-center justify-center">
                                        <Search className="mb-2 h-8 w-8 text-slate-300" />
                                        <p>No actions found matching your filters.</p>
                                        <button
                                            onClick={clearFilters}
                                            className="mt-2 text-sm font-medium text-blue-600 hover:text-blue-700 hover:underline"
                                        >
                                            Clear all filters
                                        </button>
                                    </div>
                                </td>
                            </tr>
                        )}
                    </tbody>
                </table>
            </div>
            {totalPages > 1 && (
                <CardFooter className="flex items-center justify-between border-t border-slate-100 bg-slate-50/50 px-6 py-3">
                    <div className="text-xs text-slate-500">
                        Showing <strong>{(currentPage - 1) * ITEMS_PER_PAGE + 1}</strong> to{" "}
                        <strong>
                            {Math.min(currentPage * ITEMS_PER_PAGE, filteredActions.length)}
                        </strong>{" "}
                        of <strong>{filteredActions.length}</strong> actions
                    </div>
                    <div className="flex items-center space-x-2">
                        <Button
                            variant="outline"
                            size="sm"
                            onClick={() => setCurrentPage((prev) => Math.max(prev - 1, 1))}
                            disabled={currentPage === 1}
                            className="h-8 w-8 p-0"
                        >
                            <ChevronLeft className="h-4 w-4" />
                        </Button>
                        <div className="text-xs font-medium text-slate-700">
                            Page {currentPage} of {totalPages}
                        </div>
                        <Button
                            variant="outline"
                            size="sm"
                            onClick={() => setCurrentPage((prev) => Math.min(prev + 1, totalPages))}
                            disabled={currentPage === totalPages}
                            className="h-8 w-8 p-0"
                        >
                            <ChevronRight className="h-4 w-4" />
                        </Button>
                    </div>
                </CardFooter>
            )}
        </Card>
    );
};
