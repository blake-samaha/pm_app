"use client";

import {
    useRisks,
    useResolveRisk,
    useReopenRisk,
    useRiskComments,
    useAddRiskComment,
} from "@/hooks/useRisks";
import { Risk, RiskImpact, RiskProbability, RiskStatus } from "@/types/actions-risks";
import {
    Loader2,
    ShieldAlert,
    Activity,
    ArrowRight,
    Search,
    X,
    ChevronLeft,
    ChevronRight,
    CheckCircle2,
    RotateCcw,
    MessageSquare,
    Send,
} from "lucide-react";
import { Card, CardHeader, CardTitle, CardFooter } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogHeader,
    DialogTitle,
    DialogTrigger,
} from "@/components/ui/dialog";
import ApiErrorDisplay from "@/components/ApiErrorDisplay";
import { useEffect, useState, useMemo } from "react";
import { useEffectiveUser } from "@/hooks/useEffectiveUser";
import { isCogniter } from "@/lib/permissions";
import { UserRole } from "@/types";

interface RiskListProps {
    projectId: string;
    filterByProbability?: RiskProbability | null;
    filterByImpact?: RiskImpact | null;
}

const ITEMS_PER_PAGE = 25;

const impactConfig = {
    [RiskImpact.HIGH]: {
        borderColor: "border-l-red-500",
        badge: "bg-red-50 text-red-700 ring-1 ring-inset ring-red-600/10",
        value: 3,
    },
    [RiskImpact.MEDIUM]: {
        borderColor: "border-l-amber-500",
        badge: "bg-amber-50 text-amber-700 ring-1 ring-inset ring-amber-600/10",
        value: 2,
    },
    [RiskImpact.LOW]: {
        borderColor: "border-l-emerald-500",
        badge: "bg-emerald-50 text-emerald-700 ring-1 ring-inset ring-emerald-600/10",
        value: 1,
    },
};

const probabilityConfig = {
    [RiskProbability.HIGH]: {
        style: "bg-red-50 text-red-700 ring-1 ring-inset ring-red-600/10",
        value: 3,
    },
    [RiskProbability.MEDIUM]: {
        style: "bg-amber-50 text-amber-700 ring-1 ring-inset ring-amber-600/10",
        value: 2,
    },
    [RiskProbability.LOW]: {
        style: "bg-emerald-50 text-emerald-700 ring-1 ring-inset ring-emerald-600/10",
        value: 1,
    },
};

const statusConfig = {
    [RiskStatus.OPEN]: {
        badge: "bg-blue-50 text-blue-700 ring-1 ring-inset ring-blue-600/10",
        label: "Open",
    },
    [RiskStatus.CLOSED]: {
        badge: "bg-slate-100 text-slate-600 ring-1 ring-inset ring-slate-400/10",
        label: "Closed",
    },
    [RiskStatus.MITIGATED]: {
        badge: "bg-emerald-50 text-emerald-700 ring-1 ring-inset ring-emerald-600/10",
        label: "Mitigated",
    },
};

const calculateRiskScore = (risk: Risk) => {
    const impactVal = impactConfig[risk.impact].value;
    const probVal = probabilityConfig[risk.probability].value;
    const score = impactVal * probVal;
    const percentage = (score / 9) * 100;

    let colorClass = "bg-emerald-500";
    if (score >= 6) colorClass = "bg-red-500";
    else if (score >= 3) colorClass = "bg-amber-500";

    return { score, percentage, colorClass };
};

// Risk Detail Dialog Component
const RiskDetailDialog = ({ risk, projectId }: { risk: Risk; projectId: string }) => {
    const user = useEffectiveUser();
    const canResolve = user && isCogniter(user.role as UserRole);
    const isResolved = risk.status !== RiskStatus.OPEN;

    const [showResolveForm, setShowResolveForm] = useState(false);
    const [showReopenForm, setShowReopenForm] = useState(false);
    const [resolveStatus, setResolveStatus] = useState<RiskStatus.CLOSED | RiskStatus.MITIGATED>(
        RiskStatus.CLOSED
    );
    const [decisionRecord, setDecisionRecord] = useState("");
    const [reopenReason, setReopenReason] = useState("");
    const [newComment, setNewComment] = useState("");

    const resolveRisk = useResolveRisk();
    const reopenRisk = useReopenRisk();
    const { data: comments, isLoading: commentsLoading } = useRiskComments(risk.id);
    const addComment = useAddRiskComment();

    const style = impactConfig[risk.impact];
    const { percentage, colorClass } = calculateRiskScore(risk);

    const handleResolve = async () => {
        if (!decisionRecord.trim()) return;
        try {
            await resolveRisk.mutateAsync({
                riskId: risk.id,
                status: resolveStatus,
                decision_record: decisionRecord,
            });
            setShowResolveForm(false);
            setDecisionRecord("");
        } catch (error) {
            console.error("Failed to resolve risk:", error);
        }
    };

    const handleReopen = async () => {
        if (!reopenReason.trim()) return;
        try {
            await reopenRisk.mutateAsync({
                riskId: risk.id,
                reason: reopenReason,
            });
            setShowReopenForm(false);
            setReopenReason("");
        } catch (error) {
            console.error("Failed to reopen risk:", error);
        }
    };

    const handleAddComment = async () => {
        if (!newComment.trim()) return;
        try {
            await addComment.mutateAsync({
                riskId: risk.id,
                content: newComment,
            });
            setNewComment("");
        } catch (error) {
            console.error("Failed to add comment:", error);
        }
    };

    return (
        <DialogContent className="max-h-[90vh] overflow-y-auto sm:max-w-[600px]">
            <DialogHeader>
                <div className="mb-3 flex flex-wrap items-center gap-2">
                    <span
                        className={`inline-flex items-center rounded-md px-2.5 py-1 text-xs font-medium uppercase tracking-wide ${statusConfig[risk.status].badge}`}
                    >
                        {statusConfig[risk.status].label}
                    </span>
                    <span
                        className={`inline-flex items-center rounded-md px-2.5 py-1 text-xs font-medium uppercase tracking-wide ${style.badge}`}
                    >
                        {risk.impact} Impact
                    </span>
                    <span
                        className={`inline-flex items-center rounded-md px-2.5 py-1 text-xs font-medium uppercase tracking-wide ${probabilityConfig[risk.probability].style}`}
                    >
                        {risk.probability} Probability
                    </span>
                </div>
                <DialogTitle
                    className={`text-xl font-bold leading-relaxed ${isResolved ? "text-slate-500 line-through" : "text-slate-900"}`}
                >
                    {risk.description}
                </DialogTitle>
                <DialogDescription className="text-slate-500">
                    Risk ID:{" "}
                    <span className="font-mono text-xs text-slate-400">{risk.id.slice(0, 8)}</span>
                </DialogDescription>
            </DialogHeader>

            <div className="space-y-6 py-4">
                {/* Risk Score */}
                <div className="flex items-center justify-between rounded-xl border border-slate-100 bg-slate-50 p-5 shadow-sm">
                    <div>
                        <p className="text-xs font-bold uppercase tracking-wider text-slate-500">
                            Overall Risk Score
                        </p>
                        <p className="mt-1 text-xs text-slate-400">
                            Impact ({impactConfig[risk.impact].value}) × Probability (
                            {probabilityConfig[risk.probability].value})
                        </p>
                    </div>
                    <div className="text-right">
                        <span
                            className={`text-3xl font-black tracking-tight ${colorClass.replace("bg-", "text-")}`}
                        >
                            {Math.round(percentage)}%
                        </span>
                    </div>
                </div>

                {/* Mitigation Strategy */}
                <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
                    <h4 className="mb-3 flex items-center text-sm font-bold text-slate-900">
                        <ShieldAlert className="mr-2 h-4 w-4 text-indigo-500" />
                        Mitigation Strategy
                    </h4>
                    <p className="text-sm leading-relaxed text-slate-600">
                        {risk.mitigation_plan || "No mitigation plan defined."}
                    </p>
                </div>

                {/* Resolution Details (if resolved) */}
                {isResolved && risk.decision_record && (
                    <div className="rounded-xl border border-emerald-200 bg-emerald-50 p-5 shadow-sm">
                        <h4 className="mb-3 flex items-center text-sm font-bold text-emerald-800">
                            <CheckCircle2 className="mr-2 h-4 w-4 text-emerald-600" />
                            Decision Record
                        </h4>
                        <p className="text-sm leading-relaxed text-emerald-700">
                            {risk.decision_record}
                        </p>
                        {risk.resolved_at && (
                            <p className="mt-2 text-xs text-emerald-600">
                                Resolved on {new Date(risk.resolved_at).toLocaleDateString()}
                            </p>
                        )}
                    </div>
                )}

                {/* Reopen Details (if was reopened) */}
                {risk.reopen_reason && (
                    <div className="rounded-xl border border-amber-200 bg-amber-50 p-5 shadow-sm">
                        <h4 className="mb-3 flex items-center text-sm font-bold text-amber-800">
                            <RotateCcw className="mr-2 h-4 w-4 text-amber-600" />
                            Reopen Reason
                        </h4>
                        <p className="text-sm leading-relaxed text-amber-700">
                            {risk.reopen_reason}
                        </p>
                        {risk.reopened_at && (
                            <p className="mt-2 text-xs text-amber-600">
                                Reopened on {new Date(risk.reopened_at).toLocaleDateString()}
                            </p>
                        )}
                    </div>
                )}

                {/* Resolve Risk Section (Cogniters only, OPEN risks only) */}
                {canResolve && !isResolved && (
                    <div className="rounded-xl border border-indigo-200 bg-indigo-50/50 p-5">
                        {!showResolveForm ? (
                            <Button
                                onClick={() => setShowResolveForm(true)}
                                className="w-full bg-indigo-600 hover:bg-indigo-700"
                            >
                                <CheckCircle2 className="mr-2 h-4 w-4" />
                                Resolve This Risk
                            </Button>
                        ) : (
                            <div className="space-y-4">
                                <h4 className="text-sm font-bold text-indigo-900">Resolve Risk</h4>
                                <div className="flex gap-2">
                                    <Button
                                        variant={
                                            resolveStatus === RiskStatus.CLOSED
                                                ? "default"
                                                : "outline"
                                        }
                                        size="sm"
                                        onClick={() => setResolveStatus(RiskStatus.CLOSED)}
                                    >
                                        Closed
                                    </Button>
                                    <Button
                                        variant={
                                            resolveStatus === RiskStatus.MITIGATED
                                                ? "default"
                                                : "outline"
                                        }
                                        size="sm"
                                        onClick={() => setResolveStatus(RiskStatus.MITIGATED)}
                                    >
                                        Mitigated
                                    </Button>
                                </div>
                                <textarea
                                    value={decisionRecord}
                                    onChange={(e) => setDecisionRecord(e.target.value)}
                                    placeholder="Explain how this risk was resolved or why it was accepted..."
                                    className="h-24 w-full resize-none rounded-lg border border-indigo-200 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                                />
                                <div className="flex gap-2">
                                    <Button
                                        variant="outline"
                                        size="sm"
                                        onClick={() => setShowResolveForm(false)}
                                    >
                                        Cancel
                                    </Button>
                                    <Button
                                        size="sm"
                                        onClick={handleResolve}
                                        disabled={!decisionRecord.trim() || resolveRisk.isPending}
                                    >
                                        {resolveRisk.isPending ? (
                                            <Loader2 className="h-4 w-4 animate-spin" />
                                        ) : (
                                            "Confirm Resolution"
                                        )}
                                    </Button>
                                </div>
                            </div>
                        )}
                    </div>
                )}

                {/* Reopen Risk Section (Cogniters only, resolved risks only) */}
                {canResolve && isResolved && (
                    <div className="rounded-xl border border-amber-200 bg-amber-50/50 p-5">
                        {!showReopenForm ? (
                            <Button
                                variant="outline"
                                onClick={() => setShowReopenForm(true)}
                                className="w-full border-amber-300 text-amber-700 hover:bg-amber-100"
                            >
                                <RotateCcw className="mr-2 h-4 w-4" />
                                Reopen This Risk
                            </Button>
                        ) : (
                            <div className="space-y-4">
                                <h4 className="text-sm font-bold text-amber-900">Reopen Risk</h4>
                                <textarea
                                    value={reopenReason}
                                    onChange={(e) => setReopenReason(e.target.value)}
                                    placeholder="Explain why this risk needs to be reopened..."
                                    className="h-24 w-full resize-none rounded-lg border border-amber-200 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-amber-500"
                                />
                                <div className="flex gap-2">
                                    <Button
                                        variant="outline"
                                        size="sm"
                                        onClick={() => setShowReopenForm(false)}
                                    >
                                        Cancel
                                    </Button>
                                    <Button
                                        size="sm"
                                        variant="outline"
                                        className="border-amber-300 text-amber-700 hover:bg-amber-100"
                                        onClick={handleReopen}
                                        disabled={!reopenReason.trim() || reopenRisk.isPending}
                                    >
                                        {reopenRisk.isPending ? (
                                            <Loader2 className="h-4 w-4 animate-spin" />
                                        ) : (
                                            "Confirm Reopen"
                                        )}
                                    </Button>
                                </div>
                            </div>
                        )}
                    </div>
                )}

                {/* Comments Section */}
                <div className="rounded-xl border border-slate-200 bg-white p-5">
                    <h4 className="mb-4 flex items-center text-sm font-bold text-slate-900">
                        <MessageSquare className="mr-2 h-4 w-4 text-slate-500" />
                        Comments
                        {comments && comments.length > 0 && (
                            <span className="ml-2 rounded-full bg-slate-100 px-2 py-0.5 text-xs">
                                {comments.length}
                            </span>
                        )}
                    </h4>

                    {/* Comment List */}
                    <div className="mb-4 max-h-48 space-y-3 overflow-y-auto">
                        {commentsLoading ? (
                            <div className="flex justify-center py-4">
                                <Loader2 className="h-5 w-5 animate-spin text-slate-400" />
                            </div>
                        ) : comments && comments.length > 0 ? (
                            comments.map((comment) => (
                                <div key={comment.id} className="rounded-lg bg-slate-50 p-3">
                                    <p className="text-sm text-slate-700">{comment.content}</p>
                                    <p className="mt-1 text-xs text-slate-400">
                                        {new Date(comment.created_at).toLocaleString()}
                                    </p>
                                </div>
                            ))
                        ) : (
                            <p className="py-4 text-center text-sm text-slate-400">
                                No comments yet
                            </p>
                        )}
                    </div>

                    {/* Add Comment */}
                    <div className="flex gap-2">
                        <Input
                            value={newComment}
                            onChange={(e) => setNewComment(e.target.value)}
                            placeholder="Add a comment..."
                            className="flex-1"
                            onKeyDown={(e) => {
                                if (e.key === "Enter" && !e.shiftKey) {
                                    e.preventDefault();
                                    handleAddComment();
                                }
                            }}
                        />
                        <Button
                            size="sm"
                            onClick={handleAddComment}
                            disabled={!newComment.trim() || addComment.isPending}
                        >
                            {addComment.isPending ? (
                                <Loader2 className="h-4 w-4 animate-spin" />
                            ) : (
                                <Send className="h-4 w-4" />
                            )}
                        </Button>
                    </div>
                </div>
            </div>
        </DialogContent>
    );
};

export const RiskList = ({ projectId, filterByProbability, filterByImpact }: RiskListProps) => {
    const { data: risks, isLoading, isError, error, refetch } = useRisks(projectId);
    const [searchQuery, setSearchQuery] = useState("");
    const [currentPage, setCurrentPage] = useState(1);

    // Reset to first page when filters/search change
    useEffect(() => {
        setCurrentPage(1);
    }, [searchQuery, filterByProbability, filterByImpact, projectId]);

    const filteredRisks = useMemo(() => {
        if (!risks) return [];

        let filtered = risks;

        if (filterByProbability) {
            filtered = filtered.filter((risk) => risk.probability === filterByProbability);
        }
        if (filterByImpact) {
            filtered = filtered.filter((risk) => risk.impact === filterByImpact);
        }

        if (searchQuery.trim()) {
            const query = searchQuery.toLowerCase();
            filtered = filtered.filter(
                (risk) =>
                    risk.description.toLowerCase().includes(query) ||
                    risk.mitigation_plan?.toLowerCase().includes(query) ||
                    risk.status.toLowerCase().includes(query)
            );
        }

        return filtered;
    }, [risks, searchQuery, filterByProbability, filterByImpact]);

    const sortedRisks = useMemo(() => {
        return [...filteredRisks].sort((a, b) => {
            // Sort resolved risks to the bottom
            if (a.status !== RiskStatus.OPEN && b.status === RiskStatus.OPEN) return 1;
            if (a.status === RiskStatus.OPEN && b.status !== RiskStatus.OPEN) return -1;

            const scoreA = calculateRiskScore(a).score;
            const scoreB = calculateRiskScore(b).score;
            return scoreB - scoreA;
        });
    }, [filteredRisks]);

    const totalPages = Math.ceil(sortedRisks.length / ITEMS_PER_PAGE);
    const paginatedRisks = useMemo(() => {
        const startIndex = (currentPage - 1) * ITEMS_PER_PAGE;
        return sortedRisks.slice(startIndex, startIndex + ITEMS_PER_PAGE);
    }, [sortedRisks, currentPage]);

    if (isLoading) {
        return (
            <Card className="flex h-64 items-center justify-center">
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
        <Card className="flex h-full flex-col overflow-hidden border-slate-200 shadow-sm">
            <CardHeader className="flex-shrink-0 border-b border-slate-100 bg-white px-6 py-4">
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
                                <span className="inline-flex items-center gap-1.5 rounded-full border border-indigo-200 bg-indigo-50 px-2.5 py-0.5 text-xs font-medium text-indigo-700">
                                    Filtered
                                    <X className="h-3 w-3" />
                                </span>
                            )}
                        </div>

                        {totalPages > 1 && (
                            <div className="flex items-center space-x-1 rounded-md border border-slate-100 bg-slate-50 p-0.5">
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
                    </div>
                    {hasRisks && (
                        <div className="relative">
                            <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-slate-400" />
                            <Input
                                placeholder="Search risks..."
                                value={searchQuery}
                                onChange={(e) => setSearchQuery(e.target.value)}
                                className="h-9 pl-9 text-sm"
                            />
                        </div>
                    )}
                </div>
            </CardHeader>

            <div className="min-h-[300px] flex-1 space-y-3 overflow-y-auto bg-slate-100/50 p-4">
                {!hasRisks ? (
                    <div className="flex h-full flex-col items-center justify-center py-8 text-center">
                        <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-slate-100">
                            <ShieldAlert className="h-6 w-6 text-slate-400" />
                        </div>
                        <p className="mt-3 text-sm font-medium text-slate-500">
                            No risks identified
                        </p>
                        <p className="text-xs text-slate-400">Great job! Keep monitoring.</p>
                    </div>
                ) : sortedRisks.length === 0 ? (
                    <div className="flex h-full flex-col items-center justify-center py-8 text-center text-slate-500">
                        <Search className="mb-2 h-8 w-8 text-slate-300" />
                        <p className="text-sm">No risks match your search.</p>
                    </div>
                ) : (
                    paginatedRisks.map((risk) => {
                        const style = impactConfig[risk.impact];
                        const { percentage, colorClass } = calculateRiskScore(risk);
                        const isResolved = risk.status !== RiskStatus.OPEN;

                        return (
                            <Dialog key={risk.id}>
                                <DialogTrigger asChild>
                                    <button
                                        className={`group relative flex w-full flex-col gap-3 rounded-l-sm rounded-r-lg border-y border-l-4 border-r border-slate-200 p-4 text-left transition-all hover:-translate-y-0.5 hover:shadow-md ${isResolved ? "bg-slate-50 opacity-75" : "bg-white"} ${style.borderColor}`}
                                    >
                                        <div className="flex w-full items-start justify-between">
                                            <div className="flex items-center gap-2">
                                                {isResolved && (
                                                    <CheckCircle2 className="h-4 w-4 flex-shrink-0 text-emerald-500" />
                                                )}
                                                <h4
                                                    className={`line-clamp-2 pr-4 text-sm font-semibold leading-snug transition-colors group-hover:text-indigo-600 ${isResolved ? "text-slate-500 line-through" : "text-slate-900"}`}
                                                >
                                                    {risk.description}
                                                </h4>
                                            </div>
                                            <ArrowRight className="mt-0.5 h-4 w-4 flex-shrink-0 -translate-x-2 text-slate-400 opacity-0 transition-all duration-300 group-hover:translate-x-0 group-hover:opacity-100" />
                                        </div>

                                        <div className="flex flex-wrap items-center gap-2">
                                            <span
                                                className={`inline-flex items-center rounded-md px-2 py-1 text-[10px] font-medium uppercase tracking-wide ${statusConfig[risk.status].badge}`}
                                            >
                                                {statusConfig[risk.status].label}
                                            </span>
                                            <span
                                                className={`inline-flex items-center rounded-md px-2 py-1 text-[10px] font-medium uppercase tracking-wide ${style.badge}`}
                                            >
                                                {risk.impact} Impact
                                            </span>
                                            <span
                                                className={`inline-flex items-center rounded-md px-2 py-1 text-[10px] font-medium uppercase tracking-wide ${probabilityConfig[risk.probability].style}`}
                                            >
                                                {risk.probability} Prob
                                            </span>
                                        </div>

                                        {!isResolved && (
                                            <div className="w-full space-y-1.5 pt-1">
                                                <div className="flex items-center justify-between text-[10px] font-medium uppercase tracking-wider text-slate-400">
                                                    <span>Risk Score</span>
                                                    <span
                                                        className={colorClass.replace(
                                                            "bg-",
                                                            "text-"
                                                        )}
                                                    >
                                                        {Math.round(percentage)}%
                                                    </span>
                                                </div>
                                                <div className="h-1.5 w-full overflow-hidden rounded-full bg-slate-100">
                                                    <div
                                                        className={`h-full ${colorClass} transition-all duration-500 ease-out`}
                                                        style={{ width: `${percentage}%` }}
                                                    />
                                                </div>
                                            </div>
                                        )}
                                    </button>
                                </DialogTrigger>
                                <RiskDetailDialog risk={risk} projectId={projectId} />
                            </Dialog>
                        );
                    })
                )}
            </div>
            {totalPages > 1 && (
                <CardFooter className="mt-auto flex flex-shrink-0 items-center justify-between border-t border-slate-100 bg-slate-50/50 px-6 py-3">
                    <div className="text-xs text-slate-500">
                        Showing <strong>{(currentPage - 1) * ITEMS_PER_PAGE + 1}</strong> to{" "}
                        <strong>
                            {Math.min(currentPage * ITEMS_PER_PAGE, sortedRisks.length)}
                        </strong>{" "}
                        of <strong>{sortedRisks.length}</strong> risks
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
