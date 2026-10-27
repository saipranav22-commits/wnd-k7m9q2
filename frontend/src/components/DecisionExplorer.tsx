import React, { useState } from "react";
import ReactECharts from "echarts-for-react";
import { useQuery } from "@tanstack/react-query";
import { fetchDecisions, DecisionExplorerResponse } from "../api/client";
import { Calendar, Clock, ShieldCheck, Layers, AlertCircle } from "lucide-react";

interface DecisionExplorerProps {
  decisionDate: string;
  setDecisionDate: (d: string) => void;
  cutoffTime: string;
  setCutoffTime: (t: string) => void;
}

export const DecisionExplorer: React.FC<DecisionExplorerProps> = ({
  decisionDate,
  setDecisionDate,
  cutoffTime,
  setCutoffTime,
}) => {
  const [viewMode, setViewMode] = useState<"chart" | "table">("chart");

  const { data, isLoading, isError, error } = useQuery<DecisionExplorerResponse>({
    queryKey: ["decisions", decisionDate, cutoffTime],
    queryFn: () => fetchDecisions(decisionDate, cutoffTime),
  });

  const januaryDates = Array.from({ length: 31 }, (_, i) => {
    const day = (i + 1).toString().padStart(2, "0");
    return `2026-01-${day}`;
  });

  const cutoffOptions = ["07:00", "09:00", "11:00", "12:00", "14:00", "17:00", "20:00"];

  const periods = data?.periods || [];

  // ECharts option showing uncertainty planning band (P10 to P90)
  const getUncertaintyChartOption = () => {
    const labels = periods.map((p) => `SP${p.settlement_period} (${p.start_time_local.split(" ")[1]})`);
    const forecasts = periods.map((p) => p.forecast_mw ?? null);
    const actuals = periods.map((p) => p.actual_mw ?? null);
    const p10s = periods.map((p) => p.lower_bound_p10_mw ?? null);

    // Difference between P90 and P10 for stacked area
    const pBandHeight = periods.map((p) => {
      if (p.upper_bound_p90_mw !== null && p.lower_bound_p10_mw !== null && p.upper_bound_p90_mw !== undefined && p.lower_bound_p10_mw !== undefined) {
        return Math.max(0, p.upper_bound_p90_mw - p.lower_bound_p10_mw);
      }
      return null;
    });

    return {
      backgroundColor: "transparent",
      tooltip: {
        trigger: "axis",
        backgroundColor: "#0F172A",
        borderColor: "#334155",
        textStyle: { color: "#F8FAFC", fontSize: 12 },
        formatter: (params: any) => {
          if (!params || !params.length) return "";
          const idx = params[0].dataIndex;
          const p = periods[idx];
          return `
            <div class="font-mono text-xs font-semibold mb-1 text-teal-300">
              Settlement Period ${p.settlement_period} (${p.start_time_local})
            </div>
            <div class="space-y-1 text-xs">
              <div class="flex justify-between space-x-3">
                <span class="text-teal-400">● Forecast:</span>
                <span class="font-mono font-semibold">${p.forecast_mw !== null ? `${p.forecast_mw} MW` : "N/A"}</span>
              </div>
              <div class="flex justify-between space-x-3">
                <span class="text-emerald-400">● Actual Outturn:</span>
                <span class="font-mono font-semibold">${p.actual_mw !== null ? `${p.actual_mw} MW` : "N/A"}</span>
              </div>
              <div class="flex justify-between space-x-3">
                <span class="text-amber-400">● Error:</span>
                <span class="font-mono">${p.signed_error_mw != null ? `${p.signed_error_mw > 0 ? "+" : ""}${p.signed_error_mw} MW` : "N/A"}</span>
              </div>
              <div class="border-t border-slate-700 pt-1 text-[11px] text-slate-300">
                Planning Range (P10–P90): <strong class="font-mono text-amber-300">${p.lower_bound_p10_mw} – ${p.upper_bound_p90_mw} MW</strong>
              </div>
              <div class="text-[10px] text-slate-400">
                Published: ${p.forecast_publish_time_utc ? p.forecast_publish_time_utc.replace("T", " ").replace("Z", " UTC") : "N/A"}
                (${p.lead_time_hours}h lead)
              </div>
            </div>
          `;
        },
      },
      legend: {
        data: ["Eligible Forecast", "Empirical P10 Planning Floor", "P10–P90 Planning Band", "Actual Generation"],
        textStyle: { color: "#94A3B8" },
        top: 0,
      },
      grid: { left: "3%", right: "3%", top: "12%", bottom: "12%", containLabel: true },
      xAxis: {
        type: "category",
        data: labels,
        axisLine: { lineStyle: { color: "#334155" } },
        axisLabel: {
          color: "#94A3B8",
          interval: 3, // show every 4th label (every 2 hours)
          fontSize: 10,
        },
      },
      yAxis: {
        type: "value",
        name: "Power (MW)",
        splitLine: { lineStyle: { color: "#1E293B" } },
        axisLabel: { color: "#94A3B8" },
        nameTextStyle: { color: "#94A3B8" },
      },
      series: [
        {
          name: "Empirical P10 Planning Floor",
          type: "line",
          data: p10s,
          lineStyle: { opacity: 0 },
          stack: "uncertainty-band",
          symbol: "none",
        },
        {
          name: "P10–P90 Planning Band",
          type: "line",
          data: pBandHeight,
          lineStyle: { opacity: 0 },
          stack: "uncertainty-band",
          symbol: "none",
          areaStyle: {
            color: "rgba(245, 158, 11, 0.15)", // warm amber uncertainty
          },
        },
        {
          name: "Eligible Forecast",
          type: "line",
          data: forecasts,
          lineStyle: { width: 3, color: "#14B8A6", type: "dashed" },
          itemStyle: { color: "#14B8A6" },
          symbol: "circle",
          symbolSize: 5,
        },
        {
          name: "Actual Generation",
          type: "line",
          data: actuals,
          lineStyle: { width: 2.5, color: "#10B981" },
          itemStyle: { color: "#10B981" },
          symbol: "circle",
          symbolSize: 5,
        },
      ],
    };
  };

  return (
    <div className="space-y-6">
      {/* Control Bar */}
      <div className="card-surface p-4 rounded-xl flex flex-wrap items-center justify-between gap-4">
        <div className="flex flex-wrap items-center gap-4">
          <div className="flex items-center space-x-2">
            <Calendar className="w-4 h-4 text-teal-400" />
            <label className="text-xs font-semibold uppercase tracking-wider text-slate-400">
              Decision Date:
            </label>
            <select
              value={decisionDate}
              onChange={(e) => setDecisionDate(e.target.value)}
              className="bg-navy-900 border border-slate-700 text-slate-100 text-xs sm:text-sm rounded-lg px-3 py-1.5 focus:outline-none focus:border-teal-500 font-mono"
            >
              {januaryDates.map((d) => (
                <option key={d} value={d}>
                  {d}
                </option>
              ))}
            </select>
          </div>

          <div className="flex items-center space-x-2">
            <Clock className="w-4 h-4 text-cyan-400" />
            <label className="text-xs font-semibold uppercase tracking-wider text-slate-400">
              Cutoff Time:
            </label>
            <select
              value={cutoffTime}
              onChange={(e) => setCutoffTime(e.target.value)}
              className="bg-navy-900 border border-slate-700 text-slate-100 text-xs sm:text-sm rounded-lg px-3 py-1.5 focus:outline-none focus:border-teal-500 font-mono"
            >
              {cutoffOptions.map((t) => (
                <option key={t} value={t}>
                  {t} UK Local
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* View Switcher */}
        <div className="flex items-center space-x-2">
          <button
            onClick={() => setViewMode("chart")}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
              viewMode === "chart"
                ? "bg-teal-500/20 text-teal-300 border border-teal-500/30"
                : "bg-navy-900 text-slate-400 hover:text-slate-200"
            }`}
          >
            Planning Chart
          </button>
          <button
            onClick={() => setViewMode("table")}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
              viewMode === "table"
                ? "bg-teal-500/20 text-teal-300 border border-teal-500/30"
                : "bg-navy-900 text-slate-400 hover:text-slate-200"
            }`}
          >
            48 Settlement Periods
          </button>
        </div>
      </div>

      {isLoading && (
        <div className="card-surface p-12 rounded-xl text-center text-slate-400 animate-pulse font-mono">
          Reconstructing Point-in-Time available forecasts as of {cutoffTime} UK on {decisionDate}...
        </div>
      )}

      {isError && (
        <div className="card-surface p-6 rounded-xl border-rose-500/30 bg-rose-500/10 text-rose-300 flex items-center space-x-3">
          <AlertCircle className="w-6 h-6 text-rose-400 flex-shrink-0" />
          <div>
            <div className="font-semibold text-sm">Failed to evaluate decision view</div>
            <div className="text-xs text-rose-400/80">{(error as Error)?.message}</div>
          </div>
        </div>
      )}

      {data && (
        <>
          {/* Point-in-Time Disclosure Banner */}
          <div className="card-surface p-4 rounded-xl border border-teal-500/20 bg-teal-500/5 flex items-center justify-between text-xs font-mono">
            <div className="flex items-center space-x-2 text-teal-300">
              <ShieldCheck className="w-4 h-4 text-teal-400" />
              <span>
                Point-in-Time Selection Rule: <strong className="text-white">publishTime &le; {data.cutoff_datetime_utc}</strong>
              </span>
            </div>
            <div className="text-slate-400">
              Zero Look-Ahead Bias Enforced (Latest pre-cutoff run selected)
            </div>
          </div>

          {viewMode === "chart" ? (
            /* Uncertainty Band ECharts */
            <div className="card-surface p-5 rounded-xl space-y-4">
              <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-800 pb-3">
                <div>
                  <h3 className="text-base font-bold text-white flex items-center space-x-2">
                    <Layers className="w-4 h-4 text-teal-400" />
                    <span>Day-Ahead Decision Explorer with Empirical Risk Bands</span>
                  </h3>
                  <p className="text-xs text-slate-400">
                    Shaded amber area indicates empirical P10–P90 residual range (Retrospective Backtesting Diagnostics — does not imply forward probabilistic guarantee or projected trading savings).
                  </p>
                </div>
                <div className="text-xs font-mono text-slate-400">
                  Delivery Date: <span className="text-white font-bold">{data.delivery_date}</span>
                </div>
              </div>

              <div className="h-[460px]">
                <ReactECharts option={getUncertaintyChartOption()} style={{ height: "100%", width: "100%" }} />
              </div>
            </div>
          ) : (
            /* 48 Half-Hourly Settlement Periods Table */
            <div className="card-surface rounded-xl overflow-hidden border border-slate-800">
              <div className="p-4 border-b border-slate-800 flex items-center justify-between">
                <div>
                  <h3 className="text-sm font-bold text-white">
                    Half-Hourly Settlement Periods (48 Intervals)
                  </h3>
                  <p className="text-xs text-slate-400">
                    Delivery Day: {data.delivery_date} | Forecasts fixed at {data.cutoff_time} UK
                  </p>
                </div>
                <div className="text-xs font-mono text-slate-400">
                  {periods.length} Half-Hour Periods
                </div>
              </div>

              <div className="overflow-x-auto max-h-[600px] overflow-y-auto">
                <table className="w-full text-left text-xs font-mono">
                  <thead className="bg-navy-900 sticky top-0 border-b border-slate-800 text-slate-400 text-[11px] uppercase tracking-wider">
                    <tr>
                      <th className="py-2.5 px-3">SP</th>
                      <th className="py-2.5 px-3">Delivery Time (Local)</th>
                      <th className="py-2.5 px-3">Forecast (MW)</th>
                      <th className="py-2.5 px-3">Actual (MW)</th>
                      <th className="py-2.5 px-3">Error (MW)</th>
                      <th className="py-2.5 px-3">P10 Floor</th>
                      <th className="py-2.5 px-3">P90 Ceiling</th>
                      <th className="py-2.5 px-3">Published At (UTC)</th>
                      <th className="py-2.5 px-3">Lead (h)</th>
                      <th className="py-2.5 px-3">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60 text-slate-200">
                    {periods.map((p) => (
                      <tr key={p.interval_index} className="hover:bg-slate-800/40 transition-colors">
                        <td className="py-2 px-3 font-bold text-teal-400">#{p.settlement_period}</td>
                        <td className="py-2 px-3 text-slate-300">{p.start_time_local.split(" ")[1]}</td>
                        <td className="py-2 px-3 font-bold text-teal-300">
                          {p.forecast_mw != null ? `${p.forecast_mw.toLocaleString()}` : "—"}
                        </td>
                        <td className="py-2 px-3 font-bold text-emerald-400">
                          {p.actual_mw != null ? `${p.actual_mw.toLocaleString()}` : "—"}
                        </td>
                        <td className="py-2 px-3">
                          {p.signed_error_mw != null ? (
                            <span className={p.signed_error_mw > 0 ? "text-amber-400" : "text-cyan-400"}>
                              {p.signed_error_mw > 0 ? `+${p.signed_error_mw}` : p.signed_error_mw}
                            </span>
                          ) : (
                            "—"
                          )}
                        </td>
                        <td className="py-2 px-3 text-amber-300/80">{p.lower_bound_p10_mw ?? "—"}</td>
                        <td className="py-2 px-3 text-amber-300/80">{p.upper_bound_p90_mw ?? "—"}</td>
                        <td className="py-2 px-3 text-slate-400 text-[11px]">
                          {p.forecast_publish_time_utc ? p.forecast_publish_time_utc.replace("T", " ").replace("Z", "") : "—"}
                        </td>
                        <td className="py-2 px-3 text-slate-400">{p.lead_time_hours ? `${p.lead_time_hours}h` : "—"}</td>
                        <td className="py-2 px-3">
                          <span className={p.status === "MATCHED" ? "badge-matched" : "badge-missing"}>
                            {p.status}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
};
