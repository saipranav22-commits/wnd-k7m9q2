import React from "react";
import { Wind, Activity, Database, Clock, Layers, BarChart3, FileSpreadsheet, BookOpen } from "lucide-react";
import { HealthResponse } from "../api/client";

interface NavbarProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  health?: HealthResponse;
}

export const Navbar: React.FC<NavbarProps> = ({ activeTab, setActiveTab, health }) => {
  const tabs = [
    { id: "overview", label: "Executive Overview", icon: Activity },
    { id: "decisions", label: "Day-Ahead Decision Explorer", icon: Layers },
    { id: "accuracy", label: "Forecast Accuracy Analytics", icon: BarChart3 },
    { id: "records", label: "Historical Data Explorer", icon: FileSpreadsheet },
    { id: "methodology", label: "Methodology & Provenance", icon: BookOpen },
  ];

  return (
    <header className="border-b border-slate-800 bg-navy-900/90 backdrop-blur-md sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo & Title */}
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-teal-500 to-emerald-600 flex items-center justify-center shadow-lg shadow-teal-500/20">
              <Wind className="w-6 h-6 text-white" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="text-xl font-bold tracking-tight text-white font-mono">AERIS</span>
                <span className="text-xs px-2 py-0.5 rounded-full bg-teal-500/10 text-teal-400 border border-teal-500/30 font-medium">
                  UK Wind Intelligence
                </span>
              </div>
              <p className="text-xs text-slate-400 hidden sm:block">
                Day-Ahead Wind Generation & Forecast Accuracy Platform
              </p>
            </div>
          </div>

          {/* System Health / Data Provenance Badge */}
          <div className="hidden md:flex items-center space-x-4 text-xs font-mono">
            <div className="flex items-center space-x-2 bg-navy-850 px-3 py-1.5 rounded-lg border border-slate-800">
              <Database className="w-3.5 h-3.5 text-teal-400" />
              <span className="text-slate-400">Cache:</span>
              <span className="text-emerald-400 font-semibold">
                {health?.database_connected ? "Elexon Verified" : "Connecting..."}
              </span>
              <span className="text-slate-600">|</span>
              <span className="text-slate-300">
                {health ? `${health.actual_records_count.toLocaleString()} Act / ${health.forecast_records_count.toLocaleString()} Fc` : "Loading..."}
              </span>
            </div>
            <div className="flex items-center space-x-1.5 text-slate-400 bg-navy-850 px-2.5 py-1.5 rounded-lg border border-slate-800">
              <Clock className="w-3.5 h-3.5 text-cyan-400" />
              <span>Jan 2026 Decisions</span>
            </div>
          </div>
        </div>

        {/* Navigation Tabs */}
        <nav className="flex space-x-1 overflow-x-auto py-2 -mb-px border-t border-slate-800/60 no-scrollbar">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center space-x-2 px-3 py-2 rounded-lg text-xs sm:text-sm font-medium whitespace-nowrap transition-all duration-150 ${
                  isActive
                    ? "bg-teal-500/15 text-teal-300 border border-teal-500/30 shadow-sm shadow-teal-500/10"
                    : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/50"
                }`}
              >
                <Icon className={`w-4 h-4 ${isActive ? "text-teal-400" : "text-slate-500"}`} />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </nav>
      </div>
    </header>
  );
};
