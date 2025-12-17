"use client";

import { Risk, RiskImpact, RiskProbability } from "@/types/actions-risks";
import { cn } from "@/lib/utils";

interface RiskMatrixProps {
    risks: Risk[];
    selectedCell?: { probability: RiskProbability; impact: RiskImpact } | null;
    onCellClick?: (probability: RiskProbability, impact: RiskImpact) => void;
}

export const RiskMatrix = ({ risks, selectedCell, onCellClick }: RiskMatrixProps) => {
    // Helper to filter risks for a specific cell
    const getRisksForCell = (probability: RiskProbability, impact: RiskImpact) => {
        return risks.filter(r => r.probability === probability && r.impact === impact);
    };
    
    const handleCellClick = (probability: RiskProbability, impact: RiskImpact) => {
        if (onCellClick) {
            // Toggle: if clicking the same cell, deselect it
            if (selectedCell?.probability === probability && selectedCell?.impact === impact) {
                onCellClick(probability, impact); // Will be handled as toggle in parent
            } else {
                onCellClick(probability, impact);
            }
        }
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
        <div className="flex flex-col w-full items-center justify-center p-4">
            <div className="grid grid-cols-[auto_auto_1fr] gap-x-3 w-full max-w-[500px]">
                
                {/* Y-Axis Label (Rotated) */}
                <div className="flex items-center justify-center w-6">
                    <div className="-rotate-90 text-xs font-bold text-slate-500 uppercase tracking-widest whitespace-nowrap">
                        Probability
                    </div>
                </div>

                {/* Y-Axis Row Labels (High/Med/Low) */}
                <div className="grid grid-rows-3 gap-2 h-full w-8">
                     <div className="flex items-center justify-end text-[10px] font-semibold text-slate-500 uppercase">High</div>
                     <div className="flex items-center justify-end text-[10px] font-semibold text-slate-500 uppercase">Med</div>
                     <div className="flex items-center justify-end text-[10px] font-semibold text-slate-500 uppercase">Low</div>
                </div>

                {/* The Matrix Grid */}
                <div className="grid grid-cols-3 grid-rows-3 gap-2 aspect-square w-full">
                        {cells.map((cell, index) => {
                            const cellRisks = getRisksForCell(cell.prob, cell.impact);
                            const count = cellRisks.length;
                            const isSelected = selectedCell?.probability === cell.prob && selectedCell?.impact === cell.impact;
                            
                            return (
                                <button
                                    key={index}
                                    onClick={() => handleCellClick(cell.prob, cell.impact)}
                                    className={cn(
                                        "relative flex flex-col items-center justify-center rounded-lg border-2 transition-all duration-200",
                                        "hover:scale-105 hover:shadow-lg hover:z-10",
                                        "focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-indigo-500",
                                        getSeverityColor(cell.severity),
                                        count === 0 && "opacity-40 bg-slate-50 border-slate-200 text-slate-300 cursor-not-allowed hover:scale-100 hover:shadow-none",
                                        count > 0 && "cursor-pointer border-transparent shadow-sm",
                                        isSelected && "ring-4 ring-indigo-500 ring-offset-2 scale-105 shadow-xl z-20"
                                    )}
                                    disabled={count === 0}
                                    title={`${cell.prob} Probability, ${cell.impact} Impact (${count} ${count === 1 ? 'risk' : 'risks'})`}
                                >
                                    <span className="text-2xl md:text-3xl font-bold mb-0.5">{count}</span>
                                    {count > 0 && (
                                        <span className="text-[9px] md:text-[10px] font-medium uppercase tracking-wider opacity-90">
                                            {count === 1 ? 'Risk' : 'Risks'}
                                        </span>
                                    )}
                                </button>
                            );
                        })}
                </div>

                {/* Spacers for alignment below matrix */}
                <div className="col-span-2"></div>
                
                {/* X-Axis Labels */}
                <div className="grid grid-cols-3 text-center text-[10px] font-semibold text-slate-500 uppercase tracking-wider mt-2">
                    <div>Low</div>
                    <div>Medium</div>
                    <div>High</div>
                </div>

                {/* Spacers */}
                <div className="col-span-2"></div>

                {/* X-Axis Main Label */}
                <div className="text-center text-xs font-bold text-slate-500 uppercase tracking-widest mt-3">
                    Impact
                </div>
            </div>
        </div>
    );
};

