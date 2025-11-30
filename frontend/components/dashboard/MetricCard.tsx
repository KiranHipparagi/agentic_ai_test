"use client";

import { LucideIcon, TrendingUp, TrendingDown, AlertTriangle } from "lucide-react";

interface MetricCardProps {
  title: string;
  value: string | number;
  change: string;
  trend: "up" | "down" | "alert";
  icon: LucideIcon;
  color: "blue" | "green" | "red" | "purple" | "amber" | "indigo";
}

const colorClasses = {
  blue: {
    bg: "bg-blue-50",
    text: "text-blue-600",
    icon: "bg-blue-100 text-blue-600"
  },
  green: {
    bg: "bg-green-50",
    text: "text-green-600",
    icon: "bg-green-100 text-green-600"
  },
  red: {
    bg: "bg-red-50",
    text: "text-red-600",
    icon: "bg-red-100 text-red-600"
  },
  purple: {
    bg: "bg-purple-50",
    text: "text-purple-600",
    icon: "bg-purple-100 text-purple-600"
  },
  amber: {
    bg: "bg-amber-50",
    text: "text-amber-600",
    icon: "bg-amber-100 text-amber-600"
  },
  indigo: {
    bg: "bg-indigo-50",
    text: "text-indigo-600",
    icon: "bg-indigo-100 text-indigo-600"
  }
};

export default function MetricCard({ title, value, change, trend, icon: Icon, color }: MetricCardProps) {
  const colors = colorClasses[color];
  
  const TrendIcon = trend === "up" ? TrendingUp : trend === "down" ? TrendingDown : AlertTriangle;
  const trendColor = trend === "up" ? "text-green-600" : trend === "down" ? "text-red-600" : "text-amber-600";

  return (
    <div className={`${colors.bg} rounded-lg p-3 border border-gray-200 shadow-sm hover:shadow-md transition-shadow`}>
      <div className="flex items-start justify-between mb-2">
        <div className={`${colors.icon} p-1.5 rounded-md`}>
          <Icon className="w-4 h-4" />
        </div>
        <div className={`flex items-center gap-0.5 text-[10px] font-medium ${trendColor}`}>
          <TrendIcon className="w-3 h-3" />
          {change}
        </div>
      </div>
      <div>
        <p className="text-[10px] text-gray-600 mb-0.5">{title}</p>
        <p className={`text-lg font-bold ${colors.text}`}>{value}</p>
      </div>
    </div>
  );
}
