"use client";

import { useRisks } from "@/hooks/useRisks";
import { Risk, RiskImpact, RiskProbability } from "@/types/actions-risks";
import { Loader2, ShieldAlert, Activity, ArrowRight, Search, LayoutGrid, List, X } from "lucide-react";
import { Card, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogHeader,
    DialogTitle,
    DialogTrigger,
} from "@/components/ui/dialog";
import ApiErrorDisplay from "@/components/ApiErrorDisplay";
import { useState, useMemo } from "react";
// Removed RiskMatrix import as we are moving it to a separate tab

interface RiskListProps {
    projectId: string;
    filterByProbability?: RiskProbability | null;
    filterByImpact?: RiskImpact | null;
}

const impactConfig = {
    [RiskImpact.HIGH]: {
        borderColor: "border-l-red-500",
        badge: "bg-red-50 text-red-700 ring-1 ring-inset ring-red-600/10",
        value: 3
    },
    [RiskImpact.MEDIUM]: {
        borderColor: "border-l-amber-500",
        badge: "bg-amber-50 text-amber-700 ring-1 ring-inset ring-amber-600/10",
        value: 2
    },
    [RiskImpact.LOW]: {
        borderColor: "border-l-emerald-500",
        badge: "bg-emerald-50 text-emerald-700 ring-1 ring-inset ring-emerald-600/10",
        value: 1
    },
};

const probabilityConfig = {
    [RiskProbability.HIGH]: {
        style: "bg-red-50 text-red-700 ring-1 ring-inset ring-red-600/10",
        value: 3
    },
    [RiskProbability.MEDIUM]: {
        style: "bg-amber-50 text-amber-700 ring-1 ring-inset ring-amber-600/10",
        value: 2
    },
    [RiskProbability.LOW]: {
        style: "bg-emerald-50 text-emerald-700 ring-1 ring-inset ring-emerald-600/10",
        value: 1
    },
};

const calculateRiskScore = (risk: Risk) => {
    const impactVal = impactConfig[risk.impact].value;
    const probVal = probabilityConfig[risk.probability].value;
    // Score out of 9 (3 * 3)
    const score = impactVal * probVal;
    const percentage = (score / 9) * 100;
    
    // Determine color based on score
    let colorClass = "bg-emerald-500";
    if (score >= 6) colorClass = "bg-red-500";
    else if (score >= 3) colorClass = "bg-amber-500";
    
    return { score, percentage, colorClass };
};

export const RiskList = ({ projectId, filterByProbability, filterByImpact }: RiskListProps) => {
    const { data: risks, isLoading, isError, error, refetch } = useRisks(projectId);
    const [searchQuery, setSearchQuery] = useState("");
    // Removed viewMode state

    const filteredRisks = useMemo(() => {
        if (!risks) return [];
        
        let filtered = risks;
        
        // Apply matrix filter if set
        if (filterByProbability) {
            filtered = filtered.filter(risk => risk.probability === filterByProbability);
        }
        if (filterByImpact) {
            filtered = filtered.filter(risk => risk.impact === filterByImpact);
        }
        
        // Apply search filter
        if (searchQuery.trim()) {
            const query = searchQuery.toLowerCase();
            filtered = filtered.filter(risk => 
                risk.description.toLowerCase().includes(query) ||
                risk.mitigation_plan?.toLowerCase().includes(query) ||
                risk.status.toLowerCase().includes(query)
            );
        }
        
        return filtered;
    }, [risks, searchQuery, filterByProbability, filterByImpact]);

    const sortedRisks = useMemo(() => {
        return [...filteredRisks].sort((a, b) => {
            const scoreA = calculateRiskScore(a).score;
            const scoreB = calculateRiskScore(b).score;
            return scoreB - scoreA;
        });
    }, [filteredRisks]);

    if (isLoading) {
        return (
            <Card className="h-64 flex items-center justify-center">
                <Loader2 className="h-6 w-6 animate-spin text-slate-400" />
            </Card>
        );
    }

    if (isError) {
        return (
            <ApiErrorDisplay
                title="Failed to load risks"
                error={(error as any)?.response?.data ?? error ?? "Unknown error"}
                onRetry={() => refetch()}
            />
        );
    }

    const hasRisks = risks && risks.length > 0;

    return (
        <Card className="overflow-hidden border-slate-200 shadow-sm h-full flex flex-col">
            <CardHeader className="border-b border-slate-100 bg-white px-6 py-4 flex-shrink-0">
                <div className="flex flex-col space-y-4">
                    <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-2">
                            <CardTitle className="flex items-center text-lg font-semibold text-slate-900">
                                <Activity className="mr-2 h-5 w-5 text-indigo-600" />
                                Risk Register
                            </CardTitle>
                            <span className="flex h-6 w-6 items-center justify-center rounded-full bg-slate-100 text-xs font-medium text-slate-600">
                                {filteredRisks.length}
                            </span>
                            {(filterByProbability || filterByImpact) && (
                                <span className="inline-flex items-center gap-1.5 rounded-full bg-indigo-50 px-2.5 py-0.5 text-xs font-medium text-indigo-700 border border-indigo-200">
                                    Filtered
                                    <X className="h-3 w-3" />
                                </span>
                            )}
                        </div>
                    </div>
                    {hasRisks && (
                        <div className="relative">
                            <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-slate-400" />
                            <Input
                                placeholder="Search risks..."
                                value={searchQuery}
                                onChange={(e) => setSearchQuery(e.target.value)}
                                className="pl-9 h-9 text-sm"
                            />
                        </div>
                    )}
                </div>
            </CardHeader>
            
            <div className="flex-1 overflow-y-auto p-4 space-y-3 bg-slate-100/50 min-h-[300px]">
                {!hasRisks ? (
                    <div className="flex flex-col items-center justify-center h-full py-8 text-center">
                        <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-slate-100">
                            <ShieldAlert className="h-6 w-6 text-slate-400" />
                        </div>
                        <p className="mt-3 text-sm font-medium text-slate-500">No risks identified</p>
                        <p className="text-xs text-slate-400">Great job! Keep monitoring.</p>
                    </div>
                ) : sortedRisks.length === 0 ? (
                    <div className="flex flex-col items-center justify-center h-full py-8 text-center text-slate-500">
                        <Search className="h-8 w-8 text-slate-300 mb-2" />
                        <p className="text-sm">No risks match your search.</p>
                    </div>
                ) : (
                    sortedRisks.map((risk) => {
                        const style = impactConfig[risk.impact];
                        const { percentage, colorClass } = calculateRiskScore(risk);
                        
                        return (
                            <Dialog key={risk.id}>
                                <DialogTrigger asChild>
                                    <button className={`w-full text-left group relative flex flex-col gap-3 rounded-r-lg rounded-l-sm border-y border-r border-slate-200 border-l-4 p-4 transition-all hover:shadow-md hover:-translate-y-0.5 bg-white ${style.borderColor}`}>
                                        <div className="flex items-start justify-between w-full">
                                            <h4 className="font-semibold text-slate-900 line-clamp-2 pr-4 group-hover:text-indigo-600 transition-colors text-sm leading-snug">
                                                {risk.description}
                                            </h4>
                                            <ArrowRight className="h-4 w-4 text-slate-400 opacity-0 -translate-x-2 group-hover:opacity-100 group-hover:translate-x-0 transition-all duration-300 flex-shrink-0 mt-0.5" />
                                        </div>
                                        
                                        <div className="flex items-center gap-2">
                                            <span className={`inline-flex items-center rounded-md px-2 py-1 text-[10px] font-medium uppercase tracking-wide ${style.badge}`}>
                                                {risk.impact} Impact
                                            </span>
                                            <span className={`inline-flex items-center rounded-md px-2 py-1 text-[10px] font-medium uppercase tracking-wide ${probabilityConfig[risk.probability].style}`}>
                                                {risk.probability} Prob
                                            </span>
                                        </div>

                                        {/* Risk Score Meter */}
                                        <div className="w-full space-y-1.5 pt-1">
                                            <div className="flex justify-between items-center text-[10px] font-medium tracking-wider text-slate-400 uppercase">
                                                <span>Risk Score</span>
                                                <span className={colorClass.replace('bg-', 'text-')}>{Math.round(percentage)}%</span>
                                            </div>
                                            <div className="h-1.5 w-full bg-slate-100 rounded-full overflow-hidden">
                                                <div 
                                                    className={`h-full ${colorClass} transition-all duration-500 ease-out`} 
                                                    style={{ width: `${percentage}%` }}
                                                />
                                            </div>
                                        </div>
                                    </button>
                                </DialogTrigger>
                                <DialogContent className="sm:max-w-[500px]">
                                    <DialogHeader>
                                        <div className="flex items-center gap-2 mb-3">
                                            <span className={`inline-flex items-center rounded-md px-2.5 py-1 text-xs font-medium uppercase tracking-wide ${style.badge}`}>
                                                {risk.impact} Impact
                                            </span>
                                            <span className={`inline-flex items-center rounded-md px-2.5 py-1 text-xs font-medium uppercase tracking-wide ${probabilityConfig[risk.probability].style}`}>
                                                {risk.probability} Probability
                                            </span>
                                        </div>
                                        <DialogTitle className="text-xl font-bold leading-relaxed text-slate-900">
                                            {risk.description}
                                        </DialogTitle>
                                        <DialogDescription className="text-slate-500">
                                            Risk ID: <span className="font-mono text-xs text-slate-400">{risk.id.slice(0, 8)}</span>
                                        </DialogDescription>
                                    </DialogHeader>
                                    
                                    <div className="space-y-6 py-4">
                                        <div className="rounded-xl bg-slate-50 p-5 border border-slate-100 flex items-center justify-between shadow-sm">
                                            <div>
                                                <p className="text-xs font-bold text-slate-500 uppercase tracking-wider">Overall Risk Score</p>
                                                <p className="text-xs text-slate-400 mt-1">Impact ({impactConfig[risk.impact].value}) × Probability ({probabilityConfig[risk.probability].value})</p>
                                            </div>
                                            <div className="text-right">
                                                <span className={`text-3xl font-black tracking-tight ${colorClass.replace('bg-', 'text-')}`}>
                                                    {Math.round(percentage)}%
                                                </span>
                                            </div>
                                        </div>

                                        <div className="rounded-xl bg-white p-5 border border-slate-200 shadow-sm">
                                            <h4 className="flex items-center text-sm font-bold text-slate-900 mb-3">
                                                <ShieldAlert className="mr-2 h-4 w-4 text-indigo-500" />
                                                Mitigation Strategy
                                            </h4>
                                            <p className="text-sm text-slate-600 leading-relaxed">
                                                {risk.mitigation_plan || "No mitigation plan defined."}
                                            </p>
                                        </div>

                                        <div className="grid grid-cols-2 gap-4">
                                            <div className="rounded-lg border border-slate-100 p-3 bg-slate-50/50">
                                                <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Status</p>
                                                <p className="mt-1 text-sm font-semibold text-slate-900 capitalize">{risk.status.toLowerCase().replace('_', ' ')}</p>
                                            </div>
                                            <div className="rounded-lg border border-slate-100 p-3 bg-slate-50/50">
                                                <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Owner</p>
                                                <p className="mt-1 text-sm font-semibold text-slate-900">Project Lead</p>
                                            </div>
                                        </div>
                                    </div>
                                </DialogContent>
                            </Dialog>
                        );
                    })
                )}
            </div>
        </Card>
    );
};
