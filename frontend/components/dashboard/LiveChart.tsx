"use client";

import { useEffect, useState } from "react";
import { Chart } from "react-google-charts";
import { Activity } from "lucide-react";

interface LiveChartProps {
  title: string;
  type: "line" | "bar" | "donut" | "area" | "multi-axis" | "heatmap" | "forecast" | "gauge" | "bubble";
  height: number;
}

export default function LiveChart({ title, type, height }: LiveChartProps) {
  const [data, setData] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    generateMockData();
    const interval = setInterval(generateMockData, 5000); // Update every 5s
    return () => clearInterval(interval);
  }, [type]);

  const generateMockData = () => {
    let chartData: any[] = [];

    switch (type) {
      case "line":
        chartData = [
          ["Time", "Sales"],
          ...Array.from({ length: 24 }, (_, i) => [
            `${i}:00`,
            Math.floor(Math.random() * 5000) + 10000
          ])
        ];
        break;

      case "bar":
        chartData = [
          ["Category", "Revenue"],
          ["Campaign A", Math.random() * 50000 + 20000],
          ["Campaign B", Math.random() * 50000 + 20000],
          ["Campaign C", Math.random() * 50000 + 20000],
          ["Campaign D", Math.random() * 50000 + 20000]
        ];
        break;

      case "donut":
        chartData = [
          ["Category", "Percentage"],
          ["Grocery", 35],
          ["Fast Food", 28],
          ["Non-Food", 22],
          ["Perishable", 15]
        ];
        break;

      case "area":
        chartData = [
          ["Month", "Profit", "Cost"],
          ...Array.from({ length: 12 }, (_, i) => [
            `M${i + 1}`,
            Math.random() * 40000 + 30000,
            Math.random() * 30000 + 20000
          ])
        ];
        break;

      case "multi-axis":
        chartData = [
          ["Week", "Revenue", "Orders"],
          ...Array.from({ length: 12 }, (_, i) => [
            `W${i + 1}`,
            Math.random() * 100000 + 50000,
            Math.floor(Math.random() * 500) + 200
          ])
        ];
        break;

      case "forecast":
        chartData = [
          ["Day", "Actual", "Forecast"],
          ...Array.from({ length: 14 }, (_, i) => {
            const baseValue = 15000 + Math.random() * 5000;
            return [
              `Day ${i + 1}`,
              i < 7 ? baseValue : null,
              i >= 7 ? baseValue * 1.1 : null
            ];
          })
        ];
        break;

      default:
        chartData = [["Label", "Value"], ["Data", 100]];
    }

    setData(chartData);
    setLoading(false);
  };

  const getChartOptions = () => {
    const baseOptions = {
      backgroundColor: "transparent",
      chartArea: { width: "85%", height: "70%" },
      legend: { position: "bottom", textStyle: { fontSize: 11 } },
      fontSize: 11,
      colors: ["#D04A02", "#3b82f6", "#10b981", "#f59e0b", "#8b5cf6"]
    };

    switch (type) {
      case "line":
        return {
          ...baseOptions,
          curveType: "function",
          hAxis: { textStyle: { fontSize: 10 } },
          vAxis: { textStyle: { fontSize: 10 }, format: "short" }
        };

      case "donut":
        return {
          ...baseOptions,
          pieHole: 0.4,
          pieSliceTextStyle: { fontSize: 11 }
        };

      case "area":
        return {
          ...baseOptions,
          isStacked: false,
          areaOpacity: 0.3
        };

      case "multi-axis":
        return {
          ...baseOptions,
          series: {
            0: { targetAxisIndex: 0 },
            1: { targetAxisIndex: 1 }
          },
          vAxes: {
            0: { title: "Revenue ($)", textStyle: { fontSize: 10 } },
            1: { title: "Orders", textStyle: { fontSize: 10 } }
          }
        };

      case "forecast":
        return {
          ...baseOptions,
          series: {
            0: { lineDashStyle: [0, 0] },
            1: { lineDashStyle: [4, 4] }
          }
        };

      default:
        return baseOptions;
    }
  };

  const getChartType = () => {
    switch (type) {
      case "line":
      case "forecast":
        return "LineChart";
      case "bar":
        return "ColumnChart";
      case "donut":
        return "PieChart";
      case "area":
        return "AreaChart";
      case "multi-axis":
        return "LineChart";
      default:
        return "ColumnChart";
    }
  };

  return (
    <div className="bg-white rounded-xl shadow-sm p-3 border border-gray-200">
      <div className="flex items-center justify-between mb-2">
        <h3 className="text-xs font-semibold text-gray-900">{title}</h3>
        <Activity className="w-3 h-3 text-green-500 animate-pulse" />
      </div>
      
      {loading ? (
        <div className="flex items-center justify-center" style={{ height }}>
          <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-[#D04A02]"></div>
        </div>
      ) : (
        <Chart
          chartType={getChartType()}
          data={data}
          options={getChartOptions()}
          width="100%"
          height={`${height}px`}
        />
      )}
    </div>
  );
}
