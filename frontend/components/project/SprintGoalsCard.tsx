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
            <CardHeader className="border-b bg-gradient-to-r from-indigo-50 to-purple-50 py-4">
                <CardTitle className="flex items-center text-lg font-semibold text-gray-800">
                    <Target className="mr-2 h-5 w-5 text-indigo-600" />
                    Sprint Goals
                </CardTitle>
            </CardHeader>
            <CardContent className="p-5">
                {hasGoals ? (
                    <div className="space-y-3">
                        <div className="flex items-start space-x-3">
                            <Zap className="mt-0.5 h-4 w-4 flex-shrink-0 text-amber-500" />
                            <p className="text-sm leading-relaxed text-gray-700 whitespace-pre-wrap">
                                {sprintGoals}
                            </p>
                        </div>
                    </div>
                ) : (
                    <div className="flex flex-col items-center justify-center py-6 text-center">
                        <div className="rounded-full bg-gray-100 p-3">
                            <Target className="h-6 w-6 text-gray-400" />
                        </div>
                        <p className="mt-3 text-sm font-medium text-gray-500">
                            No sprint goals set
                        </p>
                        <p className="mt-1 text-xs text-gray-400">
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

