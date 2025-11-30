"use client";

import { useState, useEffect } from "react";
import dynamic from "next/dynamic";
import { 
  TrendingUp, TrendingDown, DollarSign, Package, 
  ShoppingCart, Users, AlertTriangle, Target,
  Activity, Zap, BarChart3, PieChart, Clock
} from "lucide-react";
import MetricCard from "./MetricCard";
import LiveChart from "./LiveChart";
import DataTable from "./DataTable";
import ForecastWidget from "./ForecastWidget";
import AnomalyDetector from "./AnomalyDetector";
import SmartInsights from "./SmartInsights";

// Dynamically import USAWeatherMap with SSR disabled
const USAWeatherMap = dynamic(() => import("./USAWeatherMap"), {
  ssr: false,
  loading: () => (
    <div className="relative w-full h-64 bg-gray-100 rounded-lg flex items-center justify-center">
      <p className="text-gray-500 text-sm">Loading map...</p>
    </div>
  ),
});

type Role = "store-manager" | "cfo" | "planner" | "marketing";

interface DashboardProps {
  locationId: string;
  productId: string;
}

export default function AdvancedDashboard({ locationId, productId }: DashboardProps) {
  const [activeRole, setActiveRole] = useState<Role>("store-manager");
  const [metrics, setMetrics] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [lastUpdated, setLastUpdated] = useState<Date>(new Date());

  const roles = [
    { id: "store-manager" as Role, label: "Store Manager", icon: Package },
    { id: "cfo" as Role, label: "CFO", icon: DollarSign },
    { id: "planner" as Role, label: "Planner", icon: Target },
    { id: "marketing" as Role, label: "Marketing", icon: Users }
  ];

  useEffect(() => {
    fetchDashboardData();
    const interval = setInterval(() => {
      fetchDashboardData();
      setLastUpdated(new Date());
    }, 30000); // Update every 30s
    return () => clearInterval(interval);
  }, [activeRole, locationId]);

  const fetchDashboardData = async () => {
    try {
      const response = await fetch(
        `http://localhost:8000/api/v1/analytics/kpis?location_id=${locationId}`
      );
      const data = await response.json();
      setMetrics(data);
      setLoading(false);
    } catch (error) {
      console.error("Failed to fetch dashboard data:", error);
      setLoading(false);
    }
  };

  const renderRoleSpecificMetrics = () => {
    switch (activeRole) {
      case "store-manager":
        return <StoreManagerView metrics={metrics} />;
      case "cfo":
        return <CFOView metrics={metrics} />;
      case "planner":
        return <PlannerView metrics={metrics} />;
      case "marketing":
        return <MarketingView metrics={metrics} />;
      default:
        return null;
    }
  };

  return (
    <div className="h-full bg-gray-50 overflow-auto">
      {/* Header with Role Tabs */}
      <div className="sticky top-0 z-10 bg-white border-b border-gray-200 shadow-sm">
        <div className="px-4 py-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <h1 className="text-lg font-bold text-gray-900">Analytics Dashboard</h1>
              <div className="flex items-center gap-1 text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded">
                <Clock className="w-3 h-3" />
                Updated: {lastUpdated.toLocaleTimeString()}
              </div>
            </div>
            <div className="flex gap-1">
              {roles.map((role) => (
                <button
                  key={role.id}
                  onClick={() => setActiveRole(role.id)}
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-all ${
                    activeRole === role.id
                      ? "bg-[#D04A02] text-white shadow-md"
                      : "bg-gray-50 text-gray-600 hover:bg-gray-100"
                  }`}
                >
                  <role.icon className="w-3 h-3" />
                  {role.label}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Dashboard Content */}
      <div className="p-4 space-y-4 max-w-[1600px] mx-auto">
        {loading ? (
          <div className="flex items-center justify-center h-96">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[#D04A02]"></div>
          </div>
        ) : (
          <>
            {/* Role-Specific Metrics & Charts */}
            {renderRoleSpecificMetrics()}
          </>
        )}
      </div>
    </div>
  );
}

// Store Manager View
function StoreManagerView({ metrics }: { metrics: any }) {
  return (
    <div className="grid grid-cols-12 gap-3">
      {/* Key Metrics Grid */}
      <div className="col-span-12 grid grid-cols-4 gap-3">
        <MetricCard
          title="Today's Sales"
          value={`$${(metrics?.total_sales || 0).toLocaleString()}`}
          change="+12.5%"
          trend="up"
          icon={ShoppingCart}
          color="blue"
        />
        <MetricCard
          title="Stock Level"
          value={`${Math.round(metrics?.avg_stock_level || 0)}`}
          change="-3.2%"
          trend="down"
          icon={Package}
          color="green"
        />
        <MetricCard
          title="Low Stock Items"
          value={metrics?.low_stock_items || 0}
          change="Critical"
          trend="alert"
          icon={AlertTriangle}
          color="red"
        />
        <MetricCard
          title="Daily Foot Traffic"
          value="1,247"
          change="+8.3%"
          trend="up"
          icon={Users}
          color="purple"
        />
      </div>

      {/* Map & Insights */}
      <div className="col-span-12 lg:col-span-4 bg-white rounded-xl shadow-sm p-3 border border-gray-200 h-full">
        <h2 className="text-xs font-semibold text-gray-900 mb-2 flex items-center gap-1.5">
          <Activity className="w-3 h-3 text-[#D04A02]" />
          Live Weather Impact (USA)
        </h2>
        <USAWeatherMap />
      </div>
      <div className="col-span-12 lg:col-span-8 h-full">
        <SmartInsights role="store-manager" />
      </div>

      {/* Charts Row */}
      <div className="col-span-12 lg:col-span-6">
        <LiveChart
          title="Sales Trend (24h)"
          type="line"
          height={200}
        />
      </div>
      <div className="col-span-12 lg:col-span-6">
        <LiveChart
          title="Category Performance"
          type="donut"
          height={200}
        />
      </div>

      {/* Alerts & Inventory */}
      <div className="col-span-12 lg:col-span-6">
        <AnomalyDetector />
      </div>
      <div className="col-span-12 lg:col-span-6">
        <DataTable
          title="Critical Inventory"
          columns={["Product", "Stock", "Status"]}
          compact={true}
        />
      </div>
    </div>
  );
}

// CFO View
function CFOView({ metrics }: { metrics: any }) {
  return (
    <div className="grid grid-cols-12 gap-3">
      {/* Financial KPIs */}
      <div className="col-span-12 grid grid-cols-5 gap-3">
        <MetricCard
          title="Revenue (MTD)"
          value={`$${(metrics?.total_revenue || 0).toLocaleString()}`}
          change="+15.2%"
          trend="up"
          icon={DollarSign}
          color="green"
        />
        <MetricCard
          title="Gross Margin"
          value="42.3%"
          change="+2.1%"
          trend="up"
          icon={TrendingUp}
          color="blue"
        />
        <MetricCard
          title="EBITDA"
          value="$847K"
          change="+18.5%"
          trend="up"
          icon={BarChart3}
          color="purple"
        />
        <MetricCard
          title="Cash Flow"
          value="$1.2M"
          change="+5.3%"
          trend="up"
          icon={Activity}
          color="indigo"
        />
        <MetricCard
          title="ROI"
          value="23.4%"
          change="+3.2%"
          trend="up"
          icon={Target}
          color="amber"
        />
      </div>

      {/* Map & Insights */}
      <div className="col-span-12 lg:col-span-4 bg-white rounded-xl shadow-sm p-3 border border-gray-200 h-full">
        <h2 className="text-xs font-semibold text-gray-900 mb-2 flex items-center gap-1.5">
          <Activity className="w-3 h-3 text-[#D04A02]" />
          Live Weather Impact (USA)
        </h2>
        <USAWeatherMap />
      </div>
      <div className="col-span-12 lg:col-span-8 h-full">
        <SmartInsights role="cfo" />
      </div>

      {/* Financial Charts */}
      <div className="col-span-12 lg:col-span-4">
        <LiveChart
          title="Revenue vs Cost"
          type="multi-axis"
          height={220}
        />
      </div>
      <div className="col-span-12 lg:col-span-4">
        <LiveChart
          title="Profit Margin Trend"
          type="area"
          height={220}
        />
      </div>
      <div className="col-span-12 lg:col-span-4">
        <LiveChart
          title="Revenue by Region"
          type="bar"
          height={220}
        />
      </div>

      {/* Forecasting */}
      <div className="col-span-12 lg:col-span-6">
        <ForecastWidget
          title="30-Day Revenue Forecast"
          metric="revenue"
        />
      </div>
      <div className="col-span-12 lg:col-span-6">
        <LiveChart
          title="Cost Analysis"
          type="heatmap"
          height={200}
        />
      </div>
    </div>
  );
}

// Planner View
function PlannerView({ metrics }: { metrics: any }) {
  return (
    <div className="grid grid-cols-12 gap-3">
      {/* Supply Chain KPIs */}
      <div className="col-span-12 grid grid-cols-4 gap-3">
        <MetricCard
          title="Avg Lead Time"
          value="4.2 days"
          change="-0.5 days"
          trend="up"
          icon={Zap}
          color="green"
        />
        <MetricCard
          title="Order Accuracy"
          value="98.7%"
          change="+1.2%"
          trend="up"
          icon={Target}
          color="blue"
        />
        <MetricCard
          title="Supplier On-Time"
          value="94.3%"
          change="-2.1%"
          trend="down"
          icon={Package}
          color="amber"
        />
        <MetricCard
          title="Inventory Turnover"
          value="8.5x"
          change="+0.7x"
          trend="up"
          icon={Activity}
          color="purple"
        />
      </div>

      {/* Map & Insights */}
      <div className="col-span-12 lg:col-span-4 bg-white rounded-xl shadow-sm p-3 border border-gray-200 h-full">
        <h2 className="text-xs font-semibold text-gray-900 mb-2 flex items-center gap-1.5">
          <Activity className="w-3 h-3 text-[#D04A02]" />
          Live Weather Impact (USA)
        </h2>
        <USAWeatherMap />
      </div>
      <div className="col-span-12 lg:col-span-8 h-full">
        <SmartInsights role="planner" />
      </div>

      {/* Demand & Supply */}
      <div className="col-span-12 lg:col-span-6">
        <LiveChart
          title="Demand Forecast (14 Days)"
          type="forecast"
          height={220}
        />
      </div>
      <div className="col-span-12 lg:col-span-6">
        <LiveChart
          title="Supply Chain Efficiency"
          type="gauge"
          height={220}
        />
      </div>

      {/* Detailed Planning */}
      <div className="col-span-12 lg:col-span-6">
        <DataTable
          title="Reorder Recommendations"
          columns={["SKU", "Current", "Recommended", "Action"]}
          compact={false}
        />
      </div>
      <div className="col-span-12 lg:col-span-6">
        <AnomalyDetector />
      </div>
    </div>
  );
}

// Marketing View
function MarketingView({ metrics }: { metrics: any }) {
  return (
    <div className="grid grid-cols-12 gap-3">
      {/* Marketing KPIs */}
      <div className="col-span-12 grid grid-cols-4 gap-3">
        <MetricCard
          title="Customer Acquisition"
          value="342"
          change="+24.5%"
          trend="up"
          icon={Users}
          color="blue"
        />
        <MetricCard
          title="Conversion Rate"
          value="3.8%"
          change="+0.5%"
          trend="up"
          icon={Target}
          color="green"
        />
        <MetricCard
          title="Avg Order Value"
          value="$127"
          change="+12.3%"
          trend="up"
          icon={DollarSign}
          color="purple"
        />
        <MetricCard
          title="Customer Retention"
          value="87.2%"
          change="+3.1%"
          trend="up"
          icon={Activity}
          color="indigo"
        />
      </div>

      {/* Map & Insights */}
      <div className="col-span-12 lg:col-span-4 bg-white rounded-xl shadow-sm p-3 border border-gray-200 h-full">
        <h2 className="text-xs font-semibold text-gray-900 mb-2 flex items-center gap-1.5">
          <Activity className="w-3 h-3 text-[#D04A02]" />
          Live Weather Impact (USA)
        </h2>
        <USAWeatherMap />
      </div>
      <div className="col-span-12 lg:col-span-8 h-full">
        <SmartInsights role="marketing" />
      </div>

      {/* Campaign Performance */}
      <div className="col-span-12 lg:col-span-4">
        <LiveChart
          title="Campaign ROI"
          type="bar"
          height={200}
        />
      </div>
      <div className="col-span-12 lg:col-span-4">
        <LiveChart
          title="Channel Performance"
          type="donut"
          height={200}
        />
      </div>
      <div className="col-span-12 lg:col-span-4">
        <LiveChart
          title="Customer Segments"
          type="bubble"
          height={200}
        />
      </div>

      {/* Customer Insights */}
      <div className="col-span-12 lg:col-span-6">
        <LiveChart
          title="Customer Lifetime Value"
          type="line"
          height={200}
        />
      </div>
      <div className="col-span-12 lg:col-span-6">
        <DataTable
          title="Top Products by Revenue"
          columns={["Product", "Revenue", "Growth"]}
          compact={true}
        />
      </div>
    </div>
  );
}
