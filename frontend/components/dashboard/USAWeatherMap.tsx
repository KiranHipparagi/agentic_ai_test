"use client";

import { useMemo } from "react";
import { Chart } from "react-google-charts";

const REGIONAL_SNAPSHOT = [
  { code: "CA", name: "California", temp: 92, precip: 0.1, alert: "Heatwave advisory" },
  { code: "TX", name: "Texas", temp: 86, precip: 1.3, alert: "Severe thunderstorms" },
  { code: "FL", name: "Florida", temp: 88, precip: 2.4, alert: "Tropical moisture" },
  { code: "WA", name: "Washington", temp: 58, precip: 2.1, alert: null },
  { code: "IL", name: "Illinois", temp: 67, precip: 0.7, alert: null },
  { code: "NY", name: "New York", temp: 61, precip: 0.9, alert: "Cold front" },
  { code: "GA", name: "Georgia", temp: 79, precip: 1.1, alert: null },
  { code: "AZ", name: "Arizona", temp: 98, precip: 0.0, alert: "Extreme heat" }
];

export default function USAWeatherMap() {
  const regions = useMemo(() => {
    return REGIONAL_SNAPSHOT.map((region) => {
      const variance = (Math.random() - 0.5) * 4; // subtle variation per render
      const temp = Math.round(region.temp + variance);
      const impactScore = Math.max(20, 100 - Math.abs(temp - 70) * 2 - region.precip * 12);

      return {
        ...region,
        temp,
        impactScore: Math.round(impactScore)
      };
    });
  }, []);

  const alerts = regions.filter((region) => region.alert);

  const chartData = useMemo(() => {
    const header: (string | { type: string; role: string; p: { html: boolean } })[] = [
      "State",
      "Impact Score",
      { type: "string", role: "tooltip", p: { html: true } }
    ];

    const rows = regions.map((region) => {
      const tooltip = `
        <div style="padding:8px;font-size:12px;line-height:1.4;color:#111827;">
          <strong>${region.name}</strong><br/>
          Temp: ${region.temp}°F<br/>
          Precipitation: ${region.precip.toFixed(1)}"<br/>
          Impact: ${region.alert ?? "Stable"}
        </div>
      `;

      return [`US-${region.code}`, region.impactScore, tooltip];
    });

    return [header, ...rows];
  }, [regions]);

  const chartOptions = {
    region: "US",
    displayMode: "regions",
    resolution: "provinces",
    backgroundColor: "transparent",
    datalessRegionColor: "#F3F4F6",
    defaultColor: "#E5E7EB",
    colorAxis: { colors: ["#D1FAE5", "#34D399", "#065F46"] },
    legend: "none" as const,
    tooltip: { isHtml: true, textStyle: { color: "#111827" } },
    enableRegionInteractivity: true
  };

  const avgImpact = Math.round(
    regions.reduce((sum, region) => sum + region.impactScore, 0) / regions.length
  );

  return (
    <div className="relative">
      <div className="w-full h-64 rounded-lg overflow-hidden shadow-inner bg-white">
        <Chart
          chartType="GeoChart"
          width="100%"
          height="100%"
          data={chartData}
          options={chartOptions}
          loader={<div className="flex h-full items-center justify-center text-xs text-gray-500">Loading map...</div>}
        />
      </div>

      {/* Legend */}
      <div className="absolute bottom-2 left-2 bg-white/90 backdrop-blur-sm rounded-lg shadow-sm p-2 text-[10px]">
        <div className="font-semibold mb-1">Impact Score</div>
        <div className="flex items-center gap-1">
          <div className="w-20 h-2 bg-gradient-to-r from-emerald-100 via-emerald-400 to-emerald-700 rounded-full"></div>
        </div>
        <div className="flex justify-between text-[9px] text-gray-600 mt-0.5">
          <span>Low</span>
          <span>High</span>
        </div>
      </div>

      {/* Stats Overlay */}
      <div className="absolute top-2 right-2 bg-white/90 backdrop-blur-sm rounded-lg shadow-sm p-2 text-[10px] space-y-1">
        <div className="flex items-center justify-between gap-2">
          <span className="font-semibold text-gray-700">Active Alerts</span>
          <span className="text-red-600 font-bold">{alerts.length}</span>
        </div>
        <div className="flex items-center justify-between gap-2">
          <span className="font-semibold text-gray-700">Avg Impact</span>
          <span className="text-gray-900 font-bold">{avgImpact}%</span>
        </div>
      </div>
    </div>
  );
}
