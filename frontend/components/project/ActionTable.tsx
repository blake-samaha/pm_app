"use client";

import { useActions } from "@/hooks/useActions";
import { ActionItem, ActionStatus, Priority } from "@/types/actions-risks";
import { Loader2, CheckCircle2, Circle, Clock, Filter, X, Search } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { Checkbox } from "@/components/ui/checkbox";
import { Input } from "@/components/ui/input";
import ApiErrorDisplay from "@/components/ApiErrorDisplay";
import { useState, useMemo } from "react";

interface ActionTableProps {
    projectId: string;
}

const statusIcons = {
    [ActionStatus.TO_DO]: Circle,
    [ActionStatus.IN_PROGRESS]: Clock,
    [ActionStatus.COMPLETE]: CheckCircle2,
};

const statusColors = {
    [ActionStatus.TO_DO]: "text-slate-400",
    [ActionStatus.IN_PROGRESS]: "text-blue-500",
    [ActionStatus.COMPLETE]: "text-emerald-500",
};

const priorityColors = {
    [Priority.HIGH]: "bg-red-100 text-red-800",
    [Priority.MEDIUM]: "bg-amber-100 text-amber-800",
    [Priority.LOW]: "bg-emerald-100 text-emerald-800",
};

type FilterState = {
    statuses: ActionStatus[];
    priorities: Priority[];
    assignees: string[];
    search: string;
};

export const ActionTable = ({ projectId }: ActionTableProps) => {
    const { data: actions, isLoading, isError, error, refetch } = useActions(projectId);
    
    // Filter States
    const [filters, setFilters] = useState<FilterState>({
        statuses: [],
        priorities: [],
        assignees: [],
        search: "",
    });

    // Derived unique lists for filter options
    const uniqueAssignees = useMemo(() => {
        if (!actions) return [];
        const assignees = actions
            .map(a => a.assignee)
            .filter((a): a is string => !!a); // Filter out null/undefined
        return Array.from(new Set(assignees)).sort();
    }, [actions]);

    const filteredActions = useMemo(() => {
        if (!actions) return [];
        
        return actions.filter((action) => {
            const matchesSearch = 
                action.title.toLowerCase().includes(filters.search.toLowerCase()) ||
                (action.jira_id && action.jira_id.toLowerCase().includes(filters.search.toLowerCase()));
            
            const matchesStatus = filters.statuses.length === 0 || filters.statuses.includes(action.status);
            const matchesPriority = filters.priorities.length === 0 || filters.priorities.includes(action.priority);
            
            // Handle "Unassigned" case specially if we want to, but here checking exact match
            const matchesAssignee = filters.assignees.length === 0 || 
                (action.assignee && filters.assignees.includes(action.assignee));

            return matchesSearch && matchesStatus && matchesPriority && matchesAssignee;
        });
    }, [actions, filters]);

    const toggleFilter = (type: keyof FilterState, value: string) => {
        setFilters(prev => {
            const current = prev[type] as string[];
            const updated = current.includes(value)
                ? current.filter(item => item !== value)
                : [...current, value];
            return { ...prev, [type]: updated };
        });
    };

    const clearFilters = () => {
        setFilters({
            statuses: [],
            priorities: [],
            assignees: [],
            search: "",
        });
    };

    const hasFilters = filters.statuses.length > 0 || filters.priorities.length > 0 || filters.assignees.length > 0 || filters.search;

    if (isLoading) {
        return (
            <Card className="h-96 flex items-center justify-center">
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
                <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-4">
                        <CardTitle className="text-lg font-semibold text-slate-900">
                            Action Register
                        </CardTitle>
                        {hasFilters && (
                            <button 
                                onClick={clearFilters}
                                className="flex items-center text-xs font-medium text-slate-500 hover:text-red-600 transition-colors bg-slate-50 px-2 py-1 rounded-md border border-slate-200"
                            >
                                <X className="mr-1 h-3 w-3" />
                                Clear {filteredActions.length !== actions?.length ? 'Filters' : ''}
                            </button>
                        )}
                    </div>
                    {/* Global Search remains useful for quick title/ID lookup */}
                    <div className="relative">
                        <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-slate-400" />
                        <Input
                            placeholder="Search..."
                            value={filters.search}
                            onChange={(e) => setFilters(prev => ({ ...prev, search: e.target.value }))}
                            className="pl-9 w-[200px]"
                        />
                    </div>
                </div>
            </CardHeader>
            
            <div className="overflow-x-visible min-h-[400px]">
                <table className="min-w-full divide-y divide-slate-100">
                    <thead className="bg-slate-50/50">
                        <tr>
                            {/* Status Filter */}
                            <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-slate-500">
                                <div className="flex items-center space-x-2">
                                    <span>Status</span>
                                    <Popover>
                                        <PopoverTrigger asChild>
                                            <button className={`p-1 rounded-md hover:bg-slate-200 transition-colors ${filters.statuses.length > 0 ? 'text-blue-600 bg-blue-50' : ''}`}>
                                                <Filter className="h-3 w-3" />
                                            </button>
                                        </PopoverTrigger>
                                        <PopoverContent className="w-48 p-3" align="start">
                                            <div className="space-y-2">
                                                <h4 className="font-medium text-xs text-slate-500 mb-2 uppercase">Filter by Status</h4>
                                                {Object.values(ActionStatus).map((status) => (
                                                    <div key={status} className="flex items-center space-x-2">
                                                        <Checkbox 
                                                            id={`status-${status}`} 
                                                            checked={filters.statuses.includes(status)}
                                                            onCheckedChange={() => toggleFilter('statuses', status)}
                                                        />
                                                        <label htmlFor={`status-${status}`} className="text-sm text-slate-700 cursor-pointer select-none">
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
                                            <button className={`p-1 rounded-md hover:bg-slate-200 transition-colors ${filters.assignees.length > 0 ? 'text-blue-600 bg-blue-50' : ''}`}>
                                                <Filter className="h-3 w-3" />
                                            </button>
                                        </PopoverTrigger>
                                        <PopoverContent className="w-56 p-3" align="start">
                                            <div className="space-y-2">
                                                <h4 className="font-medium text-xs text-slate-500 mb-2 uppercase">Filter by Assignee</h4>
                                                {uniqueAssignees.length > 0 ? (
                                                    <div className="max-h-48 overflow-y-auto space-y-2">
                                                        {uniqueAssignees.map((assignee) => (
                                                            <div key={assignee} className="flex items-center space-x-2">
                                                                <Checkbox 
                                                                    id={`assignee-${assignee}`} 
                                                                    checked={filters.assignees.includes(assignee)}
                                                                    onCheckedChange={() => toggleFilter('assignees', assignee)}
                                                                />
                                                                <label htmlFor={`assignee-${assignee}`} className="text-sm text-slate-700 cursor-pointer select-none truncate">
                                                                    {assignee}
                                                                </label>
                                                            </div>
                                                        ))}
                                                    </div>
                                                ) : (
                                                    <p className="text-xs text-slate-400 italic">No assignees found</p>
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
                                            <button className={`p-1 rounded-md hover:bg-slate-200 transition-colors ${filters.priorities.length > 0 ? 'text-blue-600 bg-blue-50' : ''}`}>
                                                <Filter className="h-3 w-3" />
                                            </button>
                                        </PopoverTrigger>
                                        <PopoverContent className="w-48 p-3" align="start">
                                            <div className="space-y-2">
                                                <h4 className="font-medium text-xs text-slate-500 mb-2 uppercase">Filter by Priority</h4>
                                                {Object.values(Priority).map((priority) => (
                                                    <div key={priority} className="flex items-center space-x-2">
                                                        <Checkbox 
                                                            id={`priority-${priority}`} 
                                                            checked={filters.priorities.includes(priority)}
                                                            onCheckedChange={() => toggleFilter('priorities', priority)}
                                                        />
                                                        <label htmlFor={`priority-${priority}`} className="text-sm text-slate-700 cursor-pointer select-none">
                                                            {priority}
                                                        </label>
                                                    </div>
                                                ))}
                                            </div>
                                        </PopoverContent>
                                    </Popover>
                                </div>
                            </th>

                            <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-slate-500">
                                Due Date
                            </th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100 bg-white">
                        {filteredActions.length > 0 ? (
                            filteredActions.map((action) => {
                                const StatusIcon = statusIcons[action.status];
                                const isPastDue =
                                    action.due_date &&
                                    new Date(action.due_date) < new Date() &&
                                    action.status !== ActionStatus.COMPLETE;

                                return (
                                    <tr
                                        key={action.id}
                                        className={`group transition-colors hover:bg-slate-50/50`}
                                    >
                                        <td className="whitespace-nowrap px-6 py-4">
                                            <div className="flex items-center" title={action.status}>
                                                <StatusIcon
                                                    className={`h-5 w-5 ${statusColors[action.status]}`}
                                                />
                                            </div>
                                        </td>
                                        <td className="px-6 py-4">
                                            <div className="text-sm font-medium text-slate-900 group-hover:text-blue-600 transition-colors">
                                                {action.title}
                                            </div>
                                            {action.jira_id && (
                                                <div className="mt-0.5 flex items-center">
                                                    <span className="inline-flex items-center rounded border border-slate-200 bg-slate-50 px-1.5 py-0.5 text-[10px] font-medium text-slate-500">
                                                        {action.jira_id}
                                                    </span>
                                                </div>
                                            )}
                                        </td>
                                        <td className="whitespace-nowrap px-6 py-4 text-sm text-slate-600">
                                            {action.assignee ? (
                                                <div className="flex items-center">
                                                    <div className="mr-2 flex h-6 w-6 items-center justify-center rounded-full bg-slate-100 text-xs font-medium text-slate-600 border border-slate-200">
                                                        {action.assignee.charAt(0).toUpperCase()}
                                                    </div>
                                                    {action.assignee}
                                                </div>
                                            ) : (
                                                <span className="text-slate-400 italic">Unassigned</span>
                                            )}
                                        </td>
                                        <td className="whitespace-nowrap px-6 py-4">
                                            <span
                                                className={`inline-flex rounded-full px-2.5 py-0.5 text-xs font-medium ${priorityColors[action.priority]}`}
                                            >
                                                {action.priority}
                                            </span>
                                        </td>
                                        <td className="whitespace-nowrap px-6 py-4 text-sm">
                                            {action.due_date ? (
                                                <span className={isPastDue ? "font-medium text-red-600" : "text-slate-500"}>
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
                                <td colSpan={5} className="px-6 py-12 text-center text-slate-500">
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
        </Card>
    );
};
