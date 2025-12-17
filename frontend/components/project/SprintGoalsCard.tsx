"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Target, Zap } from "lucide-react";

interface SprintGoalsCardProps {
    sprintGoals?: string | null;
    projectId: string;
    canEdit?: boolean;
}

export const SprintGoalsCard = ({
    sprintGoals,
    projectId,
    canEdit = false,
}: SprintGoalsCardProps) => {
    const hasGoals = sprintGoals && sprintGoals.trim().length > 0;

    return (
        <Card className="overflow-hidden">
            <CardHeader className="border-b bg-gradient-to-r from-indigo-50/50 to-purple-50/50 py-4">
                <CardTitle className="flex items-center text-lg font-bold text-slate-800">
                    <Target className="mr-2 h-5 w-5 text-indigo-600" />
                    Sprint Goals
                </CardTitle>
            </CardHeader>
            <CardContent className="p-6">
                {hasGoals ? (
                    <div className="space-y-4">
                        <div className="flex items-start gap-4 rounded-lg bg-slate-50 p-4 border border-slate-100">
                            <Zap className="mt-1 h-5 w-5 flex-shrink-0 text-amber-500" />
                            <p className="text-sm leading-relaxed text-slate-700 whitespace-pre-wrap font-medium">
                                {sprintGoals}
                            </p>
                        </div>
                    </div>
                ) : (
                    <div className="flex flex-col items-center justify-center py-8 text-center">
                        <div className="rounded-full bg-slate-50 p-4 border border-slate-100">
                            <Target className="h-6 w-6 text-slate-300" />
                        </div>
                        <p className="mt-4 text-sm font-semibold text-slate-900">
                            No sprint goals set
                        </p>
                        <p className="mt-1 max-w-xs text-xs text-slate-500">
                            Sprint goals will sync from Jira when an active sprint has a goal defined.
                        </p>
                        {canEdit && (
                            <p className="mt-2 text-xs text-indigo-500">
                                You can also set goals manually in Project Settings.
                            </p>
                        )}
                    </div>
                )}
            </CardContent>
        </Card>
    );
};

