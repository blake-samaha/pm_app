import { Project } from "@/types";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import ApiErrorDisplay from "@/components/ApiErrorDisplay";
import { format, differenceInDays, isValid, parseISO } from "date-fns";

interface TimelineProps {
    project: Project;
}

export const Timeline = ({ project }: TimelineProps) => {
    const hasDates = project.start_date && project.end_date;
    
    // Parse dates safely
    const startDate = project.start_date ? parseISO(project.start_date) : null;
    const endDate = project.end_date ? parseISO(project.end_date) : null;
    const today = new Date();

    const isValidRange = startDate && endDate && isValid(startDate) && isValid(endDate);

    let progress = 0;
    let daysRemaining = 0;
    let daysTotal = 0;

    if (isValidRange) {
        daysTotal = differenceInDays(endDate, startDate);
        const daysElapsed = differenceInDays(today, startDate);
        daysRemaining = differenceInDays(endDate, today);
        
        progress = daysTotal > 0 ? Math.min(Math.max((daysElapsed / daysTotal) * 100, 0), 100) : 0;
    }

    return (
        <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-lg font-semibold text-gray-900">Timeline</CardTitle>
                {isValidRange && (
                   <span className={`rounded-full px-2 py-1 text-xs font-medium ${
                       daysRemaining < 0 
                           ? "bg-gray-100 text-gray-800" 
                           : daysRemaining < 14 
                               ? "bg-yellow-100 text-yellow-800" 
                               : "bg-blue-100 text-blue-800"
                   }`}>
                       {daysRemaining < 0 
                           ? "Completed" 
                           : `${daysRemaining} days remaining`
                       }
                   </span>
                )}
            </CardHeader>
            <CardContent className="pt-4">
                {isValidRange ? (
                    <div className="space-y-6">
                        {/* Dates Row */}
                        <div className="flex justify-between text-sm text-gray-600">
                            <div>
                                <span className="block text-xs uppercase text-gray-400 font-medium">Start</span>
                                <span className="font-semibold text-gray-900">{format(startDate, 'MMM d, yyyy')}</span>
                            </div>
                            <div className="text-right">
                                <span className="block text-xs uppercase text-gray-400 font-medium">Target End</span>
                                <span className="font-semibold text-gray-900">{format(endDate, 'MMM d, yyyy')}</span>
                            </div>
                        </div>

                        {/* Progress Bar */}
                        <div className="relative pt-2">
                            <div className="h-2 w-full overflow-hidden rounded-full bg-gray-100">
                                <div
                                    className="h-full rounded-full bg-blue-600 transition-all duration-500"
                                    style={{ width: `${progress}%` }}
                                />
                            </div>
                            
                            {/* Today Marker */}
                            {progress > 0 && progress < 100 && (
                                <div 
                                    className="absolute top-0 -ml-1 mt-1 flex flex-col items-center"
                                    style={{ left: `${progress}%` }}
                                >
                                    <div className="h-4 w-0.5 bg-gray-400 mb-1"></div>
                                    <span className="text-[10px] font-medium text-gray-500 bg-white px-1 shadow-sm rounded border border-gray-100">
                                        Today
                                    </span>
                                </div>
                            )}
                        </div>
                    </div>
                ) : (
                    <ApiErrorDisplay
                        title="Timeline unavailable"
                        error="Sync data to view project timeline."
                    />
                )}
            </CardContent>
        </Card>
    );
};
