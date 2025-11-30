"use client";

import { useEffect, useState } from "react";
import { TrendingUp, Package, AlertTriangle, DollarSign, MapPin, Calendar } from "lucide-react";

interface StatsPanelProps {
  locationId: string;
  productId: string;
  onLocationChange: (id: string) => void;
  onProductChange: (id: string) => void;
}

export default function StatsPanel({ locationId, productId }: StatsPanelProps) {
  const [kpis, setKpis] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchKPIs();
  }, [locationId]);

  const fetchKPIs = async () => {
    try {
      const response = await fetch(`http://localhost:8000/api/v1/analytics/kpis?location_id=${locationId}`);
      const data = await response.json();
      setKpis(data);
    } catch (error) {
      console.error("Failed to fetch KPIs:", error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-sm text-gray-400">Loading analytics...</div>
      </div>
    );
  }

  const metrics = [
    {
      icon: TrendingUp,
      label: "Total Sales",
      value: kpis?.total_sales?.toLocaleString() || "0",
      color: "text-amber-500",
      bg: "bg-amber-50",
      trend: "+12.5%"
    },
    {
      icon: DollarSign,
      label: "Revenue",
      value: `$${kpis?.total_revenue?.toLocaleString() || "0"}`,
      color: "text-blue-500",
      bg: "bg-blue-50",
      trend: "+8.2%"
    },
    {
      icon: Package,
      label: "Avg Stock",
      value: kpis?.avg_stock_level?.toLocaleString() || "0",
      color: "text-green-500",
      bg: "bg-green-50",
      trend: "-3.1%"
    },
    {
      icon: AlertTriangle,
      label: "Low Stock Items",
      value: kpis?.low_stock_items || "0",
      color: "text-red-500",
      bg: "bg-red-50",
      trend: "Critical"
    },
  ];

  return (
    <div className="h-full p-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Supply Chain Dashboard</h1>
        <p className="text-sm text-gray-500">Real-time insights and analytics</p>
      </div>

      {/* Compact Metrics Grid */}
      <div className="grid grid-cols-4 gap-4 mb-8">
        {metrics.map((metric, idx) => (
          <div key={idx} className="group relative">
            <div className="absolute inset-0 bg-gradient-to-r from-transparent via-gray-100 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300 rounded-lg" />
            <div className="relative p-4 border-l-4 border-gray-200 hover:border-[#D04A02] transition-all duration-200">
              <div className="flex items-start justify-between mb-3">
                <div className={`${metric.bg} ${metric.color} p-2 rounded-lg`}>
                  <metric.icon className="w-4 h-4" />
                </div>
                <span className={`text-xs font-medium ${
                  metric.trend.startsWith('+') ? 'text-green-600' : 
                  metric.trend.startsWith('-') ? 'text-red-600' : 'text-amber-600'
                }`}>
                  {metric.trend}
                </span>
              </div>
              <div>
                <p className="text-xs text-gray-500 mb-1">{metric.label}</p>
                <p className="text-2xl font-bold text-gray-900">{metric.value}</p>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Quick Stats Bar */}
      <div className="flex items-center gap-6 py-4 px-6 bg-gray-50 rounded-lg mb-8">
        <div className="flex items-center gap-2">
          <MapPin className="w-4 h-4 text-gray-400" />
          <span className="text-sm text-gray-600">Location: <strong>All Stores</strong></span>
        </div>
        <div className="w-px h-4 bg-gray-300" />
        <div className="flex items-center gap-2">
          <Calendar className="w-4 h-4 text-gray-400" />
          <span className="text-sm text-gray-600">Period: <strong>Last 30 Days</strong></span>
        </div>
        <div className="w-px h-4 bg-gray-300" />
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
          <span className="text-sm text-gray-600">Status: <strong className="text-green-600">Live</strong></span>
        </div>
      </div>

      {/* Performance Indicators */}
      <div className="space-y-3">
        <h2 className="text-sm font-semibold text-gray-700 uppercase tracking-wide mb-4">Performance Indicators</h2>
        
        <div className="flex items-center justify-between py-3 border-b border-gray-100">
          <span className="text-sm text-gray-600">Inventory Turnover</span>
          <div className="flex items-center gap-3">
            <div className="w-32 h-1.5 bg-gray-200 rounded-full overflow-hidden">
              <div className="h-full bg-green-500 rounded-full" style={{ width: '78%' }} />
            </div>
            <span className="text-sm font-semibold text-gray-900 w-12 text-right">78%</span>
          </div>
        </div>

        <div className="flex items-center justify-between py-3 border-b border-gray-100">
          <span className="text-sm text-gray-600">Order Fulfillment</span>
          <div className="flex items-center gap-3">
            <div className="w-32 h-1.5 bg-gray-200 rounded-full overflow-hidden">
              <div className="h-full bg-blue-500 rounded-full" style={{ width: '92%' }} />
            </div>
            <span className="text-sm font-semibold text-gray-900 w-12 text-right">92%</span>
          </div>
        </div>

        <div className="flex items-center justify-between py-3 border-b border-gray-100">
          <span className="text-sm text-gray-600">Supply Chain Efficiency</span>
          <div className="flex items-center gap-3">
            <div className="w-32 h-1.5 bg-gray-200 rounded-full overflow-hidden">
              <div className="h-full bg-amber-500 rounded-full" style={{ width: '85%' }} />
            </div>
            <span className="text-sm font-semibold text-gray-900 w-12 text-right">85%</span>
          </div>
        </div>

        <div className="flex items-center justify-between py-3">
          <span className="text-sm text-gray-600">Demand Forecast Accuracy</span>
          <div className="flex items-center gap-3">
            <div className="w-32 h-1.5 bg-gray-200 rounded-full overflow-hidden">
              <div className="h-full bg-purple-500 rounded-full" style={{ width: '88%' }} />
            </div>
            <span className="text-sm font-semibold text-gray-900 w-12 text-right">88%</span>
          </div>
        </div>
      </div>
    </div>
  );
}
