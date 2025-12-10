"use client";

import { useRisks } from "@/hooks/useRisks";
import { RiskImpact } from "@/types/actions-risks";
import { Loader2 } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface RiskListProps {
    projectId: string;
}

const impactColors = {
    [RiskImpact.HIGH]: "bg-red-50 border-red-200",
    [RiskImpact.MEDIUM]: "bg-yellow-50 border-yellow-200",
    [RiskImpact.LOW]: "bg-green-50 border-green-200",
};

export const RiskList = ({ projectId }: RiskListProps) => {
    const { data: risks, isLoading } = useRisks(projectId);

    if (isLoading) {
        return (
            <div className="flex h-32 items-center justify-center">
                <Loader2 className="h-6 w-6 animate-spin text-gray-400" />
            </div>
        );
    }

    if (!risks || risks.length === 0) {
        return (
            <Card>
                <CardHeader>
                    <CardTitle className="text-lg font-semibold text-gray-900">
                        Risks
                    </CardTitle>
                </CardHeader>
                <CardContent className="text-center">
                    <p className="text-gray-500">No risks identified.</p>
                </CardContent>
            </Card>
        );
    }

    return (
        <Card>
            <CardHeader>
                <CardTitle className="text-lg font-semibold text-gray-900">
                    Risk Register
                </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
                {risks.map((risk) => (
                    <div
                        key={risk.id}
                        className={`rounded-lg border p-4 ${impactColors[risk.impact]}`}
                    >
                        <div className="flex items-start justify-between">
                            <div>
                                <p className="font-medium text-gray-900">
                                    {risk.description}
                                </p>
                                {risk.mitigation_plan && (
                                    <p className="mt-2 text-sm text-gray-600">
                                        <span className="font-semibold">
                                            Mitigation:
                                        </span>{" "}
                                        {risk.mitigation_plan}
                                    </p>
                                )}
                            </div>
                            <div className="ml-4 flex flex-col items-end space-y-1 text-xs">
                                <span className="font-medium text-gray-500">
                                    Prob: {risk.probability}
                                </span>
                                <span className="font-medium text-gray-500">
                                    Impact: {risk.impact}
                                </span>
                            </div>
                        </div>
                    </div>
                ))}
            </CardContent>
        </Card>
    );
};
