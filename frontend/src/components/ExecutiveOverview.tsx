import React from "react";
import ReactECharts from "echarts-for-react";
import { useQuery } from "@tanstack/react-query";
import { fetchOverview, OverviewResponse } from "../api/client";
import { Calendar, Clock, AlertTriangle, TrendingUp, Zap } from "lucide-react";

interface ExecutiveOverviewProps {
  decisionDate: string;
  setDecisionDate: (d: string) => void;
  cutoffTime: string;
  setCutoffTime: (t: string) => void;
}

export const ExecutiveOverview: React.FC<ExecutiveOverviewProps> = ({
  decisionDate,
  setDecisionDate,
  cutoffTime,
  setCutoffTime,
}) => {
  const { data, isLoading, isError, error } = useQuery<OverviewResponse>({
    queryKey: ["overview", decisionDate, cutoffTime],
    queryFn: () => fetchOverview(decisionDate, cutoffTime),
  });

  // Generate January 2026 dates list
  const januaryDates = Array.from({ length: 31 }, (_, i) => {
    const day = (i + 1).toString().padStart(2, "0");
    return `2026-01-${day}`;
  });

  const cutoffOptions = ["07:00", "09:00", "11:00", "12:00", "14:00", "17:00", "20:00"];

  const kpis = data?.kpis;
  const timeseries = data?.timeseries || [];

  // ECharts options
  const getChartOption = () => {
    const hours = timeseries.map((t) => `${t.hour.toString().padStart(2, "0")}:00`);
    const forecasts = timeseries.map((t) => t.forecast_mw ?? null);
    const actuals = timeseries.map((t) => t.actual_mw ?? null);
    const errors = timeseries.map((t) => t.error_mw ?? null);

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
          const point = timeseries[idx];
          let html = `<div class="font-mono text-xs font-semibold mb-1 text-slate-300">
            Delivery: ${point.start_time_local} (SP ${point.settlement_period ?? idx * 2 + 1})
          </div>`;
          params.forEach((p: any) => {
            const val = p.value !== null ? `${p.value.toLocaleString()} MW` : "N/A";
            html += `<div class="flex items-center justify-between space-x-4 text-xs py-0.5">
              <span style="color:${p.color}">● ${p.seriesName}</span>
              <span class="font-mono font-medium">${val}</span>
            </div>`;
          });
          if (point.publish_time_utc) {
            html += `<div class="text-[10px] text-slate-400 mt-1 pt-1 border-t border-slate-700">
              Published: ${point.publish_time_utc.replace("T", " ").replace("Z", " UTC")}
            </div>`;
          }
          return html;
        },
      },
      legend: {
        data: ["Eligible Forecast (MW)", "Actual Outturn (MW)", "Signed Error (MW)"],
        textStyle: { color: "#94A3B8" },
        top: 0,
      },
      grid: [
        { left: "3%", right: "3%", top: "12%", height: "55%", containLabel: true },
        { left: "3%", right: "3%", top: "74%", height: "20%", containLabel: true },
      ],
      xAxis: [
        {
          type: "category",
          data: hours,
          gridIndex: 0,
          axisLine: { lineStyle: { color: "#334155" } },
          axisLabel: { color: "#94A3B8", fontSize: 11 },
        },
        {
          type: "category",
          data: hours,
          gridIndex: 1,
          axisLine: { lineStyle: { color: "#334155" } },
          axisLabel: { color: "#64748B", fontSize: 10 },
        },
      ],
      yAxis: [
        {
          type: "value",
          name: "Power (MW)",
          gridIndex: 0,
          splitLine: { lineStyle: { color: "#1E293B" } },
          axisLabel: { color: "#94A3B8" },
          nameTextStyle: { color: "#94A3B8" },
        },
        {
          type: "value",
          name: "Error (MW)",
          gridIndex: 1,
          splitLine: { lineStyle: { color: "#1E293B" } },
          axisLabel: { color: "#64748B", fontSize: 10 },
          nameTextStyle: { color: "#64748B", fontSize: 10 },
        },
      ],
      series: [
        {
          name: "Eligible Forecast (MW)",
          type: "line",
          xAxisIndex: 0,
          yAxisIndex: 0,
          data: forecasts,
          smooth: true,
          lineStyle: { width: 3, color: "#14B8A6", type: "dashed" },
          itemStyle: { color: "#14B8A6" },
          symbol: "circle",
          symbolSize: 6,
        },
        {
          name: "Actual Outturn (MW)",
          type: "line",
          xAxisIndex: 0,
          yAxisIndex: 0,
          data: actuals,
          smooth: true,
          lineStyle: { width: 3, color: "#10B981" },
          itemStyle: { color: "#10B981" },
          areaStyle: {
            color: {
              type: "linear",
              x: 0,
              y: 0,
              x2: 0,
              y2: 1,
              colorStops: [
                { offset: 0, color: "rgba(16, 185, 129, 0.25)" },
                { offset: 1, color: "rgba(16, 185, 129, 0.0)" },
              ],
            },
          },
          symbol: "circle",
          symbolSize: 6,
        },
        {
          name: "Signed Error (MW)",
          type: "bar",
          xAxisIndex: 1,
          yAxisIndex: 1,
          data: errors.map((e) => ({
            value: e,
            itemStyle: {
              color: e !== null && e > 0 ? "rgba(245, 158, 11, 0.7)" : "rgba(6, 182, 212, 0.7)",
            },
          })),
        },
      ],
    };
  };

  return (
    <div className="space-y-6">
      {/* Control Bar */}
      <div className="card-surface p-4 rounded-xl flex flex-wrap items-center justify-between gap-4">
        <div className="flex flex-wrap items-center gap-4">
          {/* Decision Date Selector */}
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

          {/* Cutoff Selector */}
          <div className="flex items-center space-x-2">
            <Clock className="w-4 h-4 text-cyan-400" />
            <label className="text-xs font-semibold uppercase tracking-wider text-slate-400">
              Cutoff Time (UK):
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

        {/* Delivery Date Target Badge */}
        {kpis && (
          <div className="flex items-center space-x-2 bg-navy-850 px-3 py-1.5 rounded-lg border border-slate-700/60 text-xs font-mono">
            <span className="text-slate-400">Target Delivery Day:</span>
            <span className="text-teal-300 font-bold">{kpis.delivery_date}</span>
            <span className="text-slate-500">|</span>
            <span className="text-emerald-400 font-medium">Cutoff: {kpis.cutoff_time} UK</span>
          </div>
        )}
      </div>

      {isLoading && (
        <div className="card-surface p-12 rounded-xl text-center text-slate-400 animate-pulse font-mono">
          Evaluating point-in-time Elexon forecasts for {decisionDate}...
        </div>
      )}

      {isError && (
        <div className="card-surface p-6 rounded-xl border-rose-500/30 bg-rose-500/10 text-rose-300 flex items-center space-x-3">
          <AlertTriangle className="w-6 h-6 text-rose-400 flex-shrink-0" />
          <div>
            <div className="font-semibold text-sm">Failed to evaluate overview</div>
            <div className="text-xs text-rose-400/80">{(error as Error)?.message}</div>
          </div>
        </div>
      )}

      {kpis && (
        <>
          {/* KPI Summary Cards */}
          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-3">
            {/* Actual Outturn MWh */}
            <div className="card-surface card-surface-hover p-4 rounded-xl">
              <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-1">
                Actual Generation
              </div>
              <div className="text-xl sm:text-2xl font-bold font-mono text-emerald-400">
                {kpis.total_actual_mwh.toLocaleString()} <span className="text-xs font-normal text-slate-400">MWh</span>
              </div>
              <div className="text-xs text-slate-400 mt-1 font-mono">
                Avg: {kpis.average_actual_mw.toLocaleString()} MW
              </div>
            </div>

            {/* Forecast MWh */}
            <div className="card-surface card-surface-hover p-4 rounded-xl">
              <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-1">
                Day-Ahead Forecast
              </div>
              <div className="text-xl sm:text-2xl font-bold font-mono text-teal-300">
                {kpis.total_forecast_mwh.toLocaleString()} <span className="text-xs font-normal text-slate-400">MWh</span>
              </div>
              <div className="text-xs text-slate-400 mt-1 font-mono">
                Avg: {kpis.average_forecast_mw.toLocaleString()} MW
              </div>
            </div>

            {/* MAE */}
            <div className="card-surface card-surface-hover p-4 rounded-xl">
              <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-1">
                Mean Abs Error (MAE)
              </div>
              <div className="text-xl sm:text-2xl font-bold font-mono text-white">
                {kpis.mae_mw.toLocaleString()} <span className="text-xs font-normal text-slate-400">MW</span>
              </div>
              <div className="text-xs text-slate-400 mt-1">Avg Volumetric Miss</div>
            </div>

            {/* RMSE */}
            <div className="card-surface card-surface-hover p-4 rounded-xl">
              <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-1">
                Root Mean Sq (RMSE)
              </div>
              <div className="text-xl sm:text-2xl font-bold font-mono text-slate-200">
                {kpis.rmse_mw.toLocaleString()} <span className="text-xs font-normal text-slate-400">MW</span>
              </div>
              <div className="text-xs text-slate-400 mt-1">Penalizes Spikes</div>
            </div>

            {/* Bias (MBE) */}
            <div className="card-surface card-surface-hover p-4 rounded-xl">
              <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-1">
                Mean Bias Error
              </div>
              <div className={`text-xl sm:text-2xl font-bold font-mono ${kpis.bias_mw > 0 ? "text-amber-400" : "text-cyan-400"}`}>
                {kpis.bias_mw > 0 ? `+${kpis.bias_mw}` : kpis.bias_mw} <span className="text-xs font-normal text-slate-400">MW</span>
              </div>
              <div className="text-xs text-slate-400 mt-1">
                {kpis.bias_mw > 0 ? "Net Overforecast" : "Net Underforecast"}
              </div>
            </div>

            {/* WAPE */}
            <div className="card-surface card-surface-hover p-4 rounded-xl">
              <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-1">
                WAPE %
              </div>
              <div className="text-xl sm:text-2xl font-bold font-mono text-white">
                {kpis.wape_percent}%
              </div>
              <div className="text-xs text-slate-400 mt-1">Weighted Error Rate</div>
            </div>

            {/* Coverage */}
            <div className="card-surface card-surface-hover p-4 rounded-xl">
              <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-1">
                Data Coverage
              </div>
              <div className="text-xl sm:text-2xl font-bold font-mono text-emerald-400">
                {kpis.coverage_percent}%
              </div>
              <div className="text-xs text-slate-400 mt-1 font-mono">
                {kpis.matched_points}/{kpis.total_points} Hours
              </div>
            </div>
          </div>

          {/* Interactive Chart */}
          <div className="card-surface p-5 rounded-xl space-y-4">
            <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-800 pb-3">
              <div>
                <h3 className="text-base font-bold text-white flex items-center space-x-2">
                  <TrendingUp className="w-4 h-4 text-teal-400" />
                  <span>Day-Ahead Available Forecast vs Outturn Actual Generation</span>
                </h3>
                <p className="text-xs text-slate-400">
                  Target Delivery: {kpis.delivery_date} | Reconstructed strictly as of {kpis.cutoff_time} UK on {kpis.decision_date}
                </p>
              </div>
              <div className="flex items-center space-x-3 text-xs font-mono">
                <span className="flex items-center space-x-1.5 text-teal-400">
                  <span className="w-2.5 h-0.5 bg-teal-400 inline-block border-t-2 border-dashed border-teal-400" />
                  <span>Forecast</span>
                </span>
                <span className="flex items-center space-x-1.5 text-emerald-400">
                  <span className="w-2.5 h-0.5 bg-emerald-400 inline-block" />
                  <span>Actual</span>
                </span>
                <span className="flex items-center space-x-1.5 text-amber-400">
                  <span className="w-2 h-2 rounded bg-amber-400 inline-block" />
                  <span>Overforecast</span>
                </span>
                <span className="flex items-center space-x-1.5 text-cyan-400">
                  <span className="w-2 h-2 rounded bg-cyan-400 inline-block" />
                  <span>Underforecast</span>
                </span>
              </div>
            </div>

            <div className="h-[420px]">
              <ReactECharts option={getChartOption()} style={{ height: "100%", width: "100%" }} />
            </div>
          </div>

          {/* Analytical Commentary */}
          <div className="card-surface p-5 rounded-xl border-l-4 border-l-teal-500 flex items-start space-x-4">
            <div className="p-2 rounded-lg bg-teal-500/10 text-teal-400 mt-0.5 flex-shrink-0">
              <Zap className="w-5 h-5" />
            </div>
            <div className="space-y-1">
              <h4 className="text-sm font-bold text-white uppercase tracking-wider">
                Trading Desk Analytical Briefing
              </h4>
              <p className="text-sm text-slate-300 leading-relaxed">
                {data.commentary}
              </p>
              <div className="text-xs text-slate-400 pt-1 font-mono flex items-center space-x-4">
                <span>Overforecast Hours: <strong className="text-amber-400">{kpis.overforecast_hours}</strong></span>
                <span>Underforecast Hours: <strong className="text-cyan-400">{kpis.underforecast_hours}</strong></span>
                <span>Cutoff UTC: <span className="text-slate-300">{kpis.cutoff_datetime_utc}</span></span>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
};
