"use client";

import { useEffect, useState } from "react";
import { TrendingUp, AlertCircle } from "lucide-react";

interface ForecastWidgetProps {
  title: string;
  metric: "revenue" | "sales" | "demand";
}

export default function ForecastWidget({ title, metric }: ForecastWidgetProps) {
  const [forecast, setForecast] = useState<any>(null);
  const [confidence, setConfidence] = useState(0);

  useEffect(() => {
    generateForecast();
    const interval = setInterval(generateForecast, 15000);
    return () => clearInterval(interval);
  }, [metric]);

  const generateForecast = () => {
    const baseValue = metric === "revenue" ? 850000 : metric === "sales" ? 12000 : 5000;
    const growth = (Math.random() * 0.3 + 0.05) * 100; // 5-35% growth
    const projected = baseValue * (1 + growth / 100);
    
    setForecast({
      current: baseValue,
      projected: projected,
      growth: growth,
      high: projected * 1.15,
      low: projected * 0.85
    });
    
    setConfidence(Math.floor(Math.random() * 15) + 80); // 80-95% confidence
  };

  if (!forecast) {
    return (
      <div className="bg-white rounded-xl shadow-lg p-6 border border-gray-200 flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[#D04A02]"></div>
      </div>
    );
  }

  const formatValue = (value: number) => {
    if (metric === "revenue") {
      return `$${(value / 1000).toFixed(0)}K`;
    }
    return value.toLocaleString();
  };

  return (
    <div className="bg-white rounded-xl shadow-lg p-6 border border-gray-200">
      <h3 className="text-sm font-semibold text-gray-900 mb-4">{title}</h3>
      
      <div className="space-y-4">
        {/* Current vs Projected */}
        <div className="flex items-center justify-between">
          <div>
            <p className="text-xs text-gray-500">Current</p>
            <p className="text-2xl font-bold text-gray-900">{formatValue(forecast.current)}</p>
          </div>
          <TrendingUp className="w-8 h-8 text-green-500" />
          <div className="text-right">
            <p className="text-xs text-gray-500">Projected</p>
            <p className="text-2xl font-bold text-[#D04A02]">{formatValue(forecast.projected)}</p>
          </div>
        </div>

        {/* Growth Indicator */}
        <div className="bg-green-50 rounded-lg p-3">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-medium text-green-700">Expected Growth</span>
            <span className="text-lg font-bold text-green-600">+{forecast.growth.toFixed(1)}%</span>
          </div>
          <div className="w-full bg-green-200 rounded-full h-2">
            <div
              className="bg-green-600 h-2 rounded-full transition-all duration-1000"
              style={{ width: `${Math.min(forecast.growth * 2, 100)}%` }}
            ></div>
          </div>
        </div>

        {/* Confidence Range */}
        <div className="grid grid-cols-2 gap-3">
          <div className="bg-blue-50 rounded-lg p-3">
            <p className="text-xs text-blue-600 mb-1">Best Case</p>
            <p className="text-lg font-semibold text-blue-700">{formatValue(forecast.high)}</p>
          </div>
          <div className="bg-amber-50 rounded-lg p-3">
            <p className="text-xs text-amber-600 mb-1">Worst Case</p>
            <p className="text-lg font-semibold text-amber-700">{formatValue(forecast.low)}</p>
          </div>
        </div>

        {/* Confidence Score */}
        <div className="flex items-center gap-2 pt-2 border-t border-gray-200">
          <AlertCircle className="w-4 h-4 text-blue-500" />
          <span className="text-xs text-gray-600">
            Confidence: <span className="font-semibold text-blue-600">{confidence}%</span>
          </span>
        </div>
      </div>
    </div>
  );
}
