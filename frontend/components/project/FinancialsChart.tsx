"use client";

import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from "recharts";

interface FinancialsChartProps {
    total: number;
    spent: number;
    remaining: number;
    currency: string;
}

export const FinancialsChart = ({ total, spent, remaining, currency }: FinancialsChartProps) => {
    const isOverBudget = remaining < 0;
    const percentSpent = total > 0 ? (spent / total) * 100 : 0;

    const data = [
        { name: "Spent", value: spent },
        { name: "Remaining", value: Math.max(0, remaining) },
    ];

    // Colors
    // If overbudget, Spent is Red. If normal, Blue. Remaining is always Slate.
    const COLORS = isOverBudget ? ["#ef4444", "#cbd5e1"] : ["#3b82f6", "#e2e8f0"];

    const formatter = new Intl.NumberFormat("en-US", {
        style: "currency",
        currency: currency,
        maximumFractionDigits: 0,
    });

    return (
        <div className="relative h-[240px] w-full">
            <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                    <Pie
                        data={data}
                        cx="50%"
                        cy="50%"
                        innerRadius="60%"
                        outerRadius="80%"
                        paddingAngle={5}
                        dataKey="value"
                        stroke="none"
                        startAngle={90}
                        endAngle={-270}
                    >
                        {data.map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                        ))}
                    </Pie>
                    <Tooltip
                        formatter={(value: number) => formatter.format(value)}
                        contentStyle={{
                            backgroundColor: "#fff",
                            borderRadius: "8px",
                            border: "1px solid #e2e8f0",
                            boxShadow: "0 4px 6px -1px rgb(0 0 0 / 0.1)",
                            outline: "none",
                        }}
                        itemStyle={{ color: "#1e293b" }}
                    />
                </PieChart>
            </ResponsiveContainer>
            {/* Centered Label */}
            <div className="pointer-events-none absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 text-center">
                <p className="text-xs font-medium uppercase tracking-wider text-slate-500">
                    Budget Used
                </p>
                <p
                    className={`text-3xl font-bold ${isOverBudget ? "text-red-600" : "text-slate-900"}`}
                >
                    {Math.round(percentSpent)}%
                </p>
            </div>
        </div>
    );
};
