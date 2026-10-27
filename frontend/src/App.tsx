import React, { useState } from "react";
import { QueryClient, QueryClientProvider, useQuery } from "@tanstack/react-query";
import { Navbar } from "./components/Navbar";
import { ExecutiveOverview } from "./components/ExecutiveOverview";
import { DecisionExplorer } from "./components/DecisionExplorer";
import { AccuracyAnalytics } from "./components/AccuracyAnalytics";
import { DataExplorer } from "./components/DataExplorer";
import { MethodologyView } from "./components/MethodologyView";
import { fetchHealth, HealthResponse } from "./api/client";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      staleTime: 1000 * 60 * 5, // 5 minutes cache
    },
  },
});

const AerisDashboard: React.FC = () => {
  const [activeTab, setActiveTab] = useState<string>("overview");
  const [decisionDate, setDecisionDate] = useState<string>("2026-01-15");
  const [cutoffTime, setCutoffTime] = useState<string>("11:00");

  const { data: health } = useQuery<HealthResponse>({
    queryKey: ["health"],
    queryFn: fetchHealth,
  });

  return (
    <div className="min-h-screen bg-navy-950 flex flex-col">
      <Navbar activeTab={activeTab} setActiveTab={setActiveTab} health={health} />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {activeTab === "overview" && (
          <ExecutiveOverview
            decisionDate={decisionDate}
            setDecisionDate={setDecisionDate}
            cutoffTime={cutoffTime}
            setCutoffTime={setCutoffTime}
          />
        )}

        {activeTab === "decisions" && (
          <DecisionExplorer
            decisionDate={decisionDate}
            setDecisionDate={setDecisionDate}
            cutoffTime={cutoffTime}
            setCutoffTime={setCutoffTime}
          />
        )}

        {activeTab === "accuracy" && (
          <AccuracyAnalytics cutoffTime={cutoffTime} />
        )}

        {activeTab === "records" && (
          <DataExplorer cutoffTime={cutoffTime} />
        )}

        {activeTab === "methodology" && (
          <MethodologyView />
        )}
      </main>

      <footer className="border-t border-slate-900 bg-navy-950 py-4 text-center text-xs text-slate-500 font-mono">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-wrap items-center justify-between gap-2">
          <span>AERIS — Wind Forecast Intelligence Platform &copy; 2026</span>
          <span className="text-slate-400">Official Elexon BMRS Data Ingestion &bull; Day-Ahead Market Backtesting</span>
          <span>Decision Scope: January 2026</span>
        </div>
      </footer>
    </div>
  );
};

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AerisDashboard />
    </QueryClientProvider>
  );
}
