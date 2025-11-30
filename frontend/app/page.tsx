"use client";

import { useState } from "react";
import { LayoutDashboard, MessageSquare, Settings, BarChart3, Book } from "lucide-react";
import ChatBox from "../components/ChatBox";
import AdvancedDashboard from "../components/dashboard/AdvancedDashboard";
import Link from "next/link";

type Tab = "dashboard" | "chat";

export default function Home() {
  const [activeTab, setActiveTab] = useState<Tab>("chat");
  const [selectedLocation, setSelectedLocation] = useState("default");
  const [selectedProduct, setSelectedProduct] = useState("default");

  const tabs = [
    { id: "dashboard" as Tab, icon: LayoutDashboard, label: "Dashboard" },
    { id: "chat" as Tab, icon: MessageSquare, label: "Chat" },
  ];

  return (
    <div className="flex h-screen bg-white">
      {/* Narrow Sidebar */}
      <aside className="w-16 bg-gradient-to-b from-gray-900 to-gray-800 flex flex-col items-center py-4 border-r border-gray-700">
        {/* Logo */}
        <div className="w-10 h-10 flex items-center justify-center mb-8 bg-white rounded-lg p-1">
          <img src="/PWC_logo.svg" alt="Logo" className="w-10 h-8" />
        </div>

        {/* Navigation */}
        <nav className="flex-1 flex flex-col gap-2">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`w-12 h-12 rounded-lg flex items-center justify-center transition-all relative group ${
                activeTab === tab.id
                  ? "bg-[#D04A02] text-white shadow-lg"
                  : "text-gray-400 hover:bg-gray-700 hover:text-white"
              }`}
              title={tab.label}
            >
              <tab.icon className="w-5 h-5" />
              {activeTab === tab.id && (
                <div className="absolute left-0 w-1 h-8 bg-white rounded-r-full" />
              )}
            </button>
          ))}
        </nav>

        {/* Documentation Button */}
        <Link 
          href="/docs" 
          className="w-12 h-12 rounded-lg flex items-center justify-center text-gray-400 hover:bg-gray-700 hover:text-white transition-all mb-4"
          title="Documentation"
        >
          <Book className="w-5 h-5" />
        </Link>

        {/* Status Indicator */}
        <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-hidden">
        {activeTab === "dashboard" && (
          <div className="h-full overflow-auto">
            <AdvancedDashboard
              locationId={selectedLocation}
              productId={selectedProduct}
            />
          </div>
        )}

        {activeTab === "chat" && (
          <div className="h-full bg-white">
            <ChatBox
              locationId={selectedLocation}
              productId={selectedProduct}
            />
          </div>
        )}
      </main>
    </div>
  );
}
