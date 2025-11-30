"use client";

import { 
  Thermometer, TrendingUp, TrendingDown, AlertTriangle, 
  Zap, ShoppingCart, Truck, DollarSign, Users, 
  Package, ArrowRight, Calendar, MapPin
} from "lucide-react";

interface SmartInsightsProps {
  role: "store-manager" | "cfo" | "planner" | "marketing";
}

export default function SmartInsights({ role }: SmartInsightsProps) {
  const renderContent = () => {
    switch (role) {
      case "store-manager":
        return <StoreManagerInsights />;
      case "cfo":
        return <CFOInsights />;
      case "planner":
        return <PlannerInsights />;
      case "marketing":
        return <MarketingInsights />;
      default:
        return null;
    }
  };

  return (
    <div className="space-y-4">
      {renderContent()}
    </div>
  );
}

// --- Store Manager Insights ---
function StoreManagerInsights() {
  return (
    <div className="space-y-4">
      {/* Hero Section */}
      <div className="bg-gradient-to-r from-orange-100 to-amber-50 rounded-xl p-4 border border-orange-200 shadow-sm">
        <div className="flex items-start gap-4">
          <div className="flex-1">
            <h3 className="text-sm font-bold text-gray-900 mb-2 flex items-center gap-2">
              <Thermometer className="w-4 h-4 text-orange-600" />
              Weather Impact Highlights
            </h3>
            <div className="flex items-center gap-3 mb-3">
              <div className="bg-white/80 rounded-lg p-2 backdrop-blur-sm">
                <span className="text-xs font-semibold text-orange-700 block">Heatwave Alert</span>
                <span className="text-[10px] text-gray-600">June 8-10 • San Francisco</span>
              </div>
              <div className="h-8 w-px bg-orange-200"></div>
              <div>
                <p className="text-xs text-gray-800">
                  <span className="font-bold text-green-600">Soda +20.6%</span> demand surge expected.
                </p>
                <p className="text-xs text-gray-800">
                  <span className="font-bold text-green-600">Ice Cream +18.3%</span> likely to rise.
                </p>
              </div>
            </div>
            <div className="bg-orange-200/50 rounded-lg p-2 flex items-center gap-2">
              <AlertTriangle className="w-3 h-3 text-orange-700" />
              <p className="text-[10px] font-medium text-orange-800">
                Soda's running low — time to restock so you don't miss out.
              </p>
            </div>
          </div>
          
          <div className="w-px bg-orange-200 self-stretch mx-2"></div>

          <div className="flex-1">
            <h3 className="text-sm font-bold text-gray-900 mb-2">Inventory & Stocking</h3>
            <ul className="space-y-2">
              <li className="text-xs text-gray-700 flex items-start gap-1.5">
                <span className="w-1 h-1 rounded-full bg-gray-400 mt-1.5"></span>
                <span>Bump up Soda by <span className="font-bold text-green-600">20%</span> and Ice Cream by <span className="font-bold text-green-600">15%</span> in San Francisco stores.</span>
              </li>
              <li className="text-xs text-gray-700 flex items-start gap-1.5">
                <span className="w-1 h-1 rounded-full bg-gray-400 mt-1.5"></span>
                <span>Slim orders for <span className="font-bold text-red-600">Tomatoes</span> & <span className="font-bold text-red-600">Salads</span>.</span>
              </li>
            </ul>
          </div>
        </div>
      </div>

      {/* Cards Grid */}
      <div className="grid grid-cols-3 gap-4">
        {/* Event Card */}
        <div className="bg-white rounded-xl p-3 border border-gray-200 shadow-sm">
          <h4 className="text-xs font-bold text-gray-900 mb-2">Pro Football event next week</h4>
          <div className="flex items-center gap-3">
            <div className="bg-blue-50 p-2 rounded-lg">
              <Zap className="w-4 h-4 text-blue-600" />
            </div>
            <p className="text-[10px] text-gray-600 leading-tight">
              Fast-track <span className="font-bold text-gray-900">Bottled Water</span> and <span className="font-bold text-gray-900">Soda</span> restocks to avoid shortages during match rush.
            </p>
          </div>
        </div>

        {/* Growth Card */}
        <div className="bg-gradient-to-br from-yellow-50 to-white rounded-xl p-3 border border-yellow-100 shadow-sm">
          <h4 className="text-xs font-bold text-gray-900 mb-2 flex items-center gap-1">
            <TrendingUp className="w-3 h-3 text-yellow-600" />
            Topline Growth
          </h4>
          <ul className="space-y-1.5">
            <li className="text-[10px] text-gray-600 leading-tight">
              • <span className="font-bold text-gray-900">Increase stock</span> for categories that regularly rise on warm-weather days.
            </li>
            <li className="text-[10px] text-gray-600 leading-tight">
              • Restock key products that historically jump <span className="font-bold text-gray-900">during rainy periods</span>.
            </li>
          </ul>
        </div>

        {/* Anomalies Card */}
        <div className="bg-white rounded-xl p-3 border border-gray-200 shadow-sm">
          <h4 className="text-xs font-bold text-gray-900 mb-2 flex items-center gap-1">
            <AlertTriangle className="w-3 h-3 text-red-500" />
            Sales Anomalies
          </h4>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xl font-bold text-red-500">↓ 20%</span>
            <span className="text-[10px] text-gray-400">vs last week</span>
          </div>
          <p className="text-[10px] text-gray-600 leading-tight">
            <span className="font-bold text-gray-900">Canned Soup</span> sales dropped likely due to warmer weather conditions.
          </p>
        </div>
      </div>

      {/* Bottom Row */}
      <div className="grid grid-cols-2 gap-4">
        <div className="bg-white rounded-xl p-3 border border-gray-200 shadow-sm">
          <h4 className="text-xs font-bold text-gray-900 mb-2">Shrinkage Risk & Waste Management</h4>
          <ul className="space-y-2">
            <li className="text-[10px] text-gray-600 flex gap-2">
              <span className="text-red-500">•</span>
              Heat raises spoilage risk for <span className="font-bold text-gray-900">Dairy</span> and <span className="font-bold text-gray-900">Fresh Produce</span>.
            </li>
            <li className="text-[10px] text-gray-600 flex gap-2">
              <span className="text-red-500">•</span>
              Tighten cold-chain and increase fridge checks for <span className="font-bold text-gray-900">Perishables</span>.
            </li>
          </ul>
        </div>

        <div className="bg-orange-50 rounded-xl p-3 border border-orange-100 shadow-sm">
          <h4 className="text-xs font-bold text-gray-900 mb-2">Customer Engagement Suggestions</h4>
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <div className="bg-white p-1.5 rounded shadow-sm">
                <ShoppingCart className="w-3 h-3 text-orange-600" />
              </div>
              <p className="text-[10px] text-gray-700">Try sending out a <span className="font-bold">digital coupon</span> next week.</p>
            </div>
            <div className="flex items-center gap-2">
              <div className="bg-white p-1.5 rounded shadow-sm">
                <Package className="w-3 h-3 text-orange-600" />
              </div>
              <p className="text-[10px] text-gray-700">Bundle deals on <span className="font-bold">Tomatoes</span> and <span className="font-bold">Baked Bread</span>.</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

// --- CFO Insights ---
function CFOInsights() {
  return (
    <div className="space-y-4">
      {/* Top Stats Row */}
      <div className="grid grid-cols-3 gap-4">
        <div className="bg-white rounded-xl p-3 border border-gray-200 shadow-sm relative overflow-hidden">
          <div className="absolute top-0 right-0 w-16 h-16 bg-green-50 rounded-bl-full -mr-4 -mt-4"></div>
          <h4 className="text-xs font-bold text-gray-500 mb-1">Regional Performance</h4>
          <div className="flex items-baseline gap-2 mb-1">
            <span className="text-2xl font-bold text-green-600">+9%</span>
            <span className="text-[10px] text-gray-400">Western North Central</span>
          </div>
          <p className="text-[10px] text-gray-600 leading-tight">
            Leads with WoW sales uplift driven by better stock planning.
          </p>
        </div>

        <div className="bg-white rounded-xl p-3 border border-gray-200 shadow-sm">
          <h4 className="text-xs font-bold text-gray-500 mb-1">Financial Risk Alerts</h4>
          <div className="mb-2">
            <span className="text-xl font-bold text-red-500">$1.3M</span>
            <p className="text-[10px] text-gray-600 leading-tight">
              Sales at risk due to stockouts in top <span className="font-bold">10 fastest-selling SKUs</span>.
            </p>
          </div>
          <div>
            <span className="text-xl font-bold text-orange-500">$900K</span>
            <p className="text-[10px] text-gray-600 leading-tight">
              High shrinkage risk in three regions for dairy perishables.
            </p>
          </div>
        </div>

        <div className="bg-white rounded-xl p-3 border border-gray-200 shadow-sm">
          <h4 className="text-xs font-bold text-gray-500 mb-1">Inventory Efficiency</h4>
          <div className="flex items-baseline gap-2 mb-1">
            <span className="text-2xl font-bold text-gray-900">14%</span>
            <span className="text-[10px] text-gray-400">vs last week</span>
          </div>
          <p className="text-[10px] text-gray-600 mb-2">
            Stockout rate rose, impacting <span className="font-bold">~6,500 units</span> of lost sales value.
          </p>
          <div className="pt-2 border-t border-gray-100">
            <span className="text-xl font-bold text-gray-900">$2.1M</span>
            <p className="text-[10px] text-gray-600">Overstock levels grew in Northwest region.</p>
          </div>
        </div>
      </div>

      {/* Middle Row */}
      <div className="grid grid-cols-2 gap-4">
        <div className="bg-white rounded-xl p-3 border border-gray-200 shadow-sm">
          <h4 className="text-xs font-bold text-gray-900 mb-3">Weather-Driven Demand Insights</h4>
          <div className="space-y-3">
            <div className="flex gap-3">
              <div className="bg-blue-50 p-2 rounded-lg h-fit">
                <Thermometer className="w-4 h-4 text-blue-600" />
              </div>
              <p className="text-[10px] text-gray-600 leading-tight">
                Heavy rain forecast expected to reduce footfall causing <span className="font-bold text-red-500">-10%</span> demand decline in ready-to-eat category in <span className="font-bold">6 markets</span>.
              </p>
            </div>
            <div className="flex gap-3">
              <div className="bg-blue-50 p-2 rounded-lg h-fit">
                <Zap className="w-4 h-4 text-blue-600" />
              </div>
              <p className="text-[10px] text-gray-600 leading-tight">
                Cold spell in Northeast projected to increase Coffee & Tea demand by <span className="font-bold text-green-600">+35%</span> vs normal.
              </p>
            </div>
          </div>
        </div>

        <div className="bg-gradient-to-br from-orange-50 to-white rounded-xl p-3 border border-orange-100 shadow-sm">
          <div className="flex items-center justify-between mb-3">
            <h4 className="text-xs font-bold text-gray-900">Executive Quick View (Top Alerts)</h4>
            <AlertTriangle className="w-4 h-4 text-orange-500 animate-pulse" />
          </div>
          <div className="space-y-2">
            <div className="bg-white p-2 rounded border border-orange-100 shadow-sm">
              <p className="text-[10px] text-gray-700">
                Stock Health: <span className="font-bold text-red-500">14%</span> SKUs understocked; <span className="font-bold text-red-500">$2.1M</span> overstocked
              </p>
            </div>
            <div className="bg-white p-2 rounded border border-orange-100 shadow-sm">
              <p className="text-[10px] text-gray-700">
                Revenue at Risk: Chicago <span className="font-bold text-red-500">$1.3M</span> due to stockouts
              </p>
            </div>
            <div className="bg-white p-2 rounded border border-orange-100 shadow-sm">
              <p className="text-[10px] text-gray-700">
                Supply Delay Warning: Frozen Foods facing <span className="font-bold text-red-500">18%</span> delivery delay
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

// --- Planner Insights ---
function PlannerInsights() {
  return (
    <div className="space-y-4">
      {/* Top Stats Row */}
      <div className="grid grid-cols-3 gap-4">
        <div className="bg-white rounded-xl p-3 border border-gray-200 shadow-sm">
          <div className="flex items-center gap-2 mb-2">
            <AlertTriangle className="w-4 h-4 text-red-500" />
            <h4 className="text-xs font-bold text-gray-700">Service Risk (Next 7 Days)</h4>
          </div>
          <span className="text-2xl font-bold text-gray-900">14%</span>
          <p className="text-[10px] text-gray-600 mt-1 leading-tight">
            <span className="font-bold">Perishable SKUs</span> in Northeast carrying less than <span className="font-bold">2 weeks</span> of cover.
          </p>
        </div>

        <div className="bg-white rounded-xl p-3 border border-gray-200 shadow-sm">
          <div className="flex items-center gap-2 mb-2">
            <Package className="w-4 h-4 text-blue-500" />
            <h4 className="text-xs font-bold text-gray-700">Transferable Inventory</h4>
          </div>
          <span className="text-2xl font-bold text-gray-900">400K</span>
          <p className="text-[10px] text-gray-600 mt-1 leading-tight">
            Units of <span className="font-bold">Salad Kits</span> can be reallocated from Chicago to Minneapolis to <span className="font-bold">avoid waste</span>.
          </p>
        </div>

        <div className="bg-white rounded-xl p-3 border border-gray-200 shadow-sm">
          <div className="flex items-center gap-2 mb-2">
            <TrendingUp className="w-4 h-4 text-green-500" />
            <h4 className="text-xs font-bold text-gray-700">Rebalancing Benefit</h4>
          </div>
          <span className="text-2xl font-bold text-gray-900">$320K</span>
          <p className="text-[10px] text-gray-600 mt-1 leading-tight">
            Redistribution of <span className="font-bold">Fresh Milk</span> can recover in lost sales regionally.
          </p>
        </div>
      </div>

      {/* Action Plan Row */}
      <div className="grid grid-cols-2 gap-4">
        <div className="bg-white rounded-xl p-3 border border-gray-200 shadow-sm">
          <h4 className="text-xs font-bold text-gray-900 mb-3">Next-Shipment Priority List</h4>
          <div className="bg-blue-50 rounded-lg p-3">
            <p className="text-[10px] text-gray-700 leading-relaxed">
              Update inbound schedule for <span className="font-bold">3 high-demand SKUs</span> (Ice Cream, Salads, Fresh Milk).
            </p>
          </div>
          <div className="mt-3">
            <h5 className="text-[10px] font-bold text-gray-700 mb-1">Inter-Store Transfer Plan</h5>
            <p className="text-[10px] text-gray-600">
              Redistribution will reduce Chicago overstock by <span className="font-bold">14%</span> and boost Detroit service by <span className="font-bold">+10%</span>.
            </p>
          </div>
        </div>

        <div className="bg-gradient-to-br from-yellow-50 to-white rounded-xl p-3 border border-yellow-100 shadow-sm">
          <h4 className="text-xs font-bold text-gray-900 mb-3">Executive Quick View (Top Alerts)</h4>
          <div className="space-y-2">
            <div className="bg-white p-2 rounded border border-yellow-100 shadow-sm flex gap-2">
              <div className="w-1 bg-red-500 rounded-full"></div>
              <p className="text-[10px] text-gray-700">
                Service Gap Alert: <span className="font-bold">10 stores</span> 20% below regional fill rate.
              </p>
            </div>
            <div className="bg-white p-2 rounded border border-yellow-100 shadow-sm flex gap-2">
              <div className="w-1 bg-orange-500 rounded-full"></div>
              <p className="text-[10px] text-gray-700">
                Overstock Alert: <span className="font-bold">Fast Foods</span> piling up in Northeast.
              </p>
            </div>
            <div className="bg-white p-2 rounded border border-yellow-100 shadow-sm flex gap-2">
              <div className="w-1 bg-blue-500 rounded-full"></div>
              <p className="text-[10px] text-gray-700">
                Replenishment Alert: Ice Cream shipments delayed - <span className="font-bold">shortage</span> risk.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

// --- Marketing Insights ---
function MarketingInsights() {
  return (
    <div className="space-y-4">
      {/* Opportunity Cards */}
      <div className="grid grid-cols-4 gap-3">
        <div className="bg-white rounded-xl p-3 border border-gray-200 shadow-sm">
          <Thermometer className="w-4 h-4 text-orange-500 mb-2" />
          <h4 className="text-[10px] font-bold text-gray-500 mb-1">Weather Opportunity</h4>
          <span className="text-xl font-bold text-green-600">+14%</span>
          <p className="text-[10px] text-gray-600 mt-1 leading-tight">
            Heatwave in South Central to boost <span className="font-bold">Cold Beverages</span>.
          </p>
        </div>

        <div className="bg-white rounded-xl p-3 border border-gray-200 shadow-sm">
          <Package className="w-4 h-4 text-blue-500 mb-2" />
          <h4 className="text-[10px] font-bold text-gray-500 mb-1">Service Risk</h4>
          <span className="text-xl font-bold text-green-600">+10%</span>
          <p className="text-[10px] text-gray-600 mt-1 leading-tight">
            <span className="font-bold">Bottled Water</span> SKUs in Southeast show low inbound.
          </p>
        </div>

        <div className="bg-white rounded-xl p-3 border border-gray-200 shadow-sm">
          <Zap className="w-4 h-4 text-yellow-500 mb-2" />
          <h4 className="text-[10px] font-bold text-gray-500 mb-1">Assortment Gap</h4>
          <span className="text-xl font-bold text-green-600">+15%</span>
          <p className="text-[10px] text-gray-600 mt-1 leading-tight">
            Surge in demand leading to gaps in <span className="font-bold">soda</span> supply.
          </p>
        </div>

        <div className="bg-white rounded-xl p-3 border border-gray-200 shadow-sm">
          <TrendingUp className="w-4 h-4 text-green-500 mb-2" />
          <h4 className="text-[10px] font-bold text-gray-500 mb-1">Category Mix</h4>
          <span className="text-xl font-bold text-green-600">+6%</span>
          <p className="text-[10px] text-gray-600 mt-1 leading-tight">
            <span className="font-bold">Beverages revenue</span> share rose MoM.
          </p>
        </div>
      </div>

      {/* Strategy Row */}
      <div className="grid grid-cols-2 gap-4">
        <div className="bg-white rounded-xl p-3 border border-gray-200 shadow-sm">
          <h4 className="text-xs font-bold text-gray-900 mb-3">Temporary Range Introduction</h4>
          <p className="text-[10px] text-gray-600 mb-3">
            Launch short-term <span className="font-bold">dessert</span> variants to meet rising demand during <span className="font-bold">Southeast heatwave</span>.
          </p>
          <div className="bg-gray-50 p-2 rounded-lg">
            <h5 className="text-[10px] font-bold text-gray-700 mb-1">Assortment Depth & Mix</h5>
            <p className="text-[10px] text-gray-600">
              Increase <span className="font-bold">Ice Cream</span> assortment by <span className="font-bold text-green-600">+20%</span> in high-growth Southeast clusters.
            </p>
          </div>
        </div>

        <div className="bg-gradient-to-br from-orange-50 to-white rounded-xl p-3 border border-orange-100 shadow-sm">
          <h4 className="text-xs font-bold text-gray-900 mb-3">Executive Quick View (Top Alerts)</h4>
          <div className="space-y-2">
            <div className="bg-white p-2 rounded border border-orange-100 shadow-sm">
              <p className="text-[10px] text-gray-700">
                Seasonal Opportunity: Warm spell may lift <span className="font-bold">Desserts</span> demand by <span className="font-bold text-green-600">+12%</span>.
              </p>
            </div>
            <div className="bg-white p-2 rounded border border-orange-100 shadow-sm">
              <p className="text-[10px] text-gray-700">
                Southeast markets see <span className="font-bold text-green-600">+10% smoothie surge</span> during heatwave.
              </p>
            </div>
            <div className="bg-white p-2 rounded border border-orange-100 shadow-sm">
              <p className="text-[10px] text-gray-700">
                Promotion Timing: Current offers expire <span className="font-bold">5 days</span> before festival.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
