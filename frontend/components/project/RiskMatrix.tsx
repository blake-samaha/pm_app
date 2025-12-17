"use client";

import { Risk, RiskImpact, RiskProbability } from "@/types/actions-risks";
import { cn } from "@/lib/utils";

interface RiskMatrixProps {
    risks: Risk[];
}

export const RiskMatrix = ({ risks }: RiskMatrixProps) => {
    // Helper to filter risks for a specific cell
    const getRisksForCell = (probability: RiskProbability, impact: RiskImpact) => {
        return risks.filter(r => r.probability === probability && r.impact === impact);
    };

    // Cell configuration
    const cells = [
        // Top Row (High Probability)
        { prob: RiskProbability.HIGH, impact: RiskImpact.LOW, severity: "medium" },
        { prob: RiskProbability.HIGH, impact: RiskImpact.MEDIUM, severity: "high" },
        { prob: RiskProbability.HIGH, impact: RiskImpact.HIGH, severity: "critical" },
        
        // Middle Row (Medium Probability)
        { prob: RiskProbability.MEDIUM, impact: RiskImpact.LOW, severity: "low" },
        { prob: RiskProbability.MEDIUM, impact: RiskImpact.MEDIUM, severity: "medium" },
        { prob: RiskProbability.MEDIUM, impact: RiskImpact.HIGH, severity: "high" },

        // Bottom Row (Low Probability)
        { prob: RiskProbability.LOW, impact: RiskImpact.LOW, severity: "low" },
        { prob: RiskProbability.LOW, impact: RiskImpact.MEDIUM, severity: "low" },
        { prob: RiskProbability.LOW, impact: RiskImpact.HIGH, severity: "medium" },
    ];

    const getSeverityColor = (severity: string) => {
        switch (severity) {
            case "critical": return "bg-red-500 text-white border-red-600";
            case "high": return "bg-red-400 text-white border-red-500";
            case "medium": return "bg-amber-400 text-white border-amber-500";
            case "low": return "bg-emerald-400 text-white border-emerald-500";
            default: return "bg-slate-100 text-slate-500";
        }
    };

    return (
        <div className="flex flex-col h-full w-full p-4 items-center justify-center">
            <div className="relative grid grid-cols-[auto_1fr] gap-2 w-full max-w-[350px]">
                
                {/* Y-Axis Label */}
                <div className="row-span-2 flex items-center justify-center -rotate-90 text-xs font-bold text-slate-400 uppercase tracking-widest h-[300px]">
                    Probability
                </div>

                {/* The Matrix Grid */}
                <div className="grid grid-rows-[auto_1fr] gap-2">
                    
                    {/* Grid Content */}
                    <div className="grid grid-cols-3 grid-rows-3 gap-1 h-[300px] w-full">
                        {cells.map((cell, index) => {
                            const cellRisks = getRisksForCell(cell.prob, cell.impact);
                            const count = cellRisks.length;
                            
                            return (
                                <div 
                                    key={index}
                                    className={cn(
                                        "relative flex items-center justify-center rounded-md border-b-4 transition-all hover:brightness-110",
                                        getSeverityColor(cell.severity),
                                        count === 0 && "opacity-30 bg-slate-200 border-slate-300 text-slate-400"
                                    )}
                                    title={`Prob: ${cell.prob}, Impact: ${cell.impact} (${count} risks)`}
                                >
                                    <span className="text-2xl font-bold">{count}</span>
                                    {/* Axis Guides inside cells for context if needed */}
                                </div>
                            );
                        })}
                    </div>

                    {/* X-Axis Labels */}
                    <div className="grid grid-cols-3 text-center text-[10px] font-medium text-slate-400 uppercase tracking-wider mt-1">
                        <div>Low</div>
                        <div>Med</div>
                        <div>High</div>
                    </div>
                </div>
            </div>
            
            {/* X-Axis Main Label */}
            <div className="text-xs font-bold text-slate-400 uppercase tracking-widest mt-1 ml-6">
                Impact
            </div>

            {/* Y-Axis Row Labels (Absolute positioning relative to grid container or sidebar) */}
            {/* For simplicity in this layout, we rely on the heatmap logic, but we could add side labels "High/Med/Low" */}
        </div>
    );
};

