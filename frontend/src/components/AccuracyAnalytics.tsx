import React, { useState } from "react";
import ReactECharts from "echarts-for-react";
import { useQuery } from "@tanstack/react-query";
import { fetchAccuracy, AccuracyResponse } from "../api/client";
import { BarChart3, TrendingUp, ScatterChart, Clock, Calendar, Info, AlertTriangle } from "lucide-react";

interface AccuracyAnalyticsProps {
  cutoffTime: string;
}

export const AccuracyAnalytics: React.FC<AccuracyAnalyticsProps> = ({ cutoffTime }) => {
  const [dateFrom, setDateFrom] = useState("2026-01-01");
  const [dateTo, setDateTo] = useState("2026-01-31");

  const { data, isLoading, isError, error } = useQuery<AccuracyResponse>({
    queryKey: ["accuracy", dateFrom, dateTo, cutoffTime],
    queryFn: () => fetchAccuracy(dateFrom, dateTo, cutoffTime),
  });

  const januaryDates = Array.from({ length: 31 }, (_, i) => {
    const day = (i + 1).toString().padStart(2, "0");
    return `2026-01-${day}`;
  });

  // Daily Trend Option
  const getDailyTrendOption = () => {
    if (!data?.daily_metrics) return {};
    const dates = data.daily_metrics.map((d) => d.delivery_date.slice(5)); // MM-DD
    const maes = data.daily_metrics.map((d) => d.mae_mw);
    const rmses = data.daily_metrics.map((d) => d.rmse_mw);
    const biases = data.daily_metrics.map((d) => d.bias_mw);

    return {
      backgroundColor: "transparent",
      tooltip: {
        trigger: "axis",
        backgroundColor: "#0F172A",
        borderColor: "#334155",
        textStyle: { color: "#F8FAFC", fontSize: 12 },
      },
      legend: {
        data: ["MAE (MW)", "RMSE (MW)", "Bias (MBE, MW)"],
        textStyle: { color: "#94A3B8" },
        top: 0,
      },
      grid: { left: "3%", right: "3%", top: "15%", bottom: "10%", containLabel: true },
      xAxis: {
        type: "category",
        data: dates,
        axisLine: { lineStyle: { color: "#334155" } },
        axisLabel: { color: "#94A3B8", fontSize: 10, rotate: 30 },
      },
      yAxis: {
        type: "value",
        name: "MW",
        splitLine: { lineStyle: { color: "#1E293B" } },
        axisLabel: { color: "#94A3B8" },
        nameTextStyle: { color: "#94A3B8" },
      },
      series: [
        {
          name: "MAE (MW)",
          type: "line",
          data: maes,
          smooth: true,
          lineStyle: { width: 2.5, color: "#14B8A6" },
          itemStyle: { color: "#14B8A6" },
        },
        {
          name: "RMSE (MW)",
          type: "line",
          data: rmses,
          smooth: true,
          lineStyle: { width: 2.5, color: "#06B6D4" },
          itemStyle: { color: "#06B6D4" },
        },
        {
          name: "Bias (MBE, MW)",
          type: "bar",
          data: biases.map((b) => ({
            value: b,
            itemStyle: {
              color: b > 0 ? "rgba(245, 158, 11, 0.7)" : "rgba(16, 185, 129, 0.7)",
            },
          })),
        },
      ],
    };
  };

  // Hour-of-Day Option
  const getHourlyOption = () => {
    if (!data?.hourly_metrics) return {};
    const hours = data.hourly_metrics.map((h) => `${h.hour.toString().padStart(2, "0")}:00`);
    const maes = data.hourly_metrics.map((h) => h.mae_mw);
    const biases = data.hourly_metrics.map((h) => h.bias_mw);

    return {
      backgroundColor: "transparent",
      tooltip: {
        trigger: "axis",
        backgroundColor: "#0F172A",
        borderColor: "#334155",
        textStyle: { color: "#F8FAFC", fontSize: 12 },
      },
      legend: {
        data: ["Hourly MAE (MW)", "Hourly Bias (MW)"],
        textStyle: { color: "#94A3B8" },
        top: 0,
      },
      grid: { left: "3%", right: "3%", top: "15%", bottom: "10%", containLabel: true },
      xAxis: {
        type: "category",
        data: hours,
        axisLine: { lineStyle: { color: "#334155" } },
        axisLabel: { color: "#94A3B8", fontSize: 10 },
      },
      yAxis: {
        type: "value",
        name: "MW",
        splitLine: { lineStyle: { color: "#1E293B" } },
        axisLabel: { color: "#94A3B8" },
        nameTextStyle: { color: "#94A3B8" },
      },
      series: [
        {
          name: "Hourly MAE (MW)",
          type: "line",
          data: maes,
          smooth: true,
          lineStyle: { width: 3, color: "#10B981" },
          itemStyle: { color: "#10B981" },
        },
        {
          name: "Hourly Bias (MW)",
          type: "bar",
          data: biases.map((b) => ({
            value: b,
            itemStyle: {
              color: b > 0 ? "rgba(245, 158, 11, 0.6)" : "rgba(6, 182, 212, 0.6)",
            },
          })),
        },
      ],
    };
  };

  // Error Distribution Histogram
  const getHistogramOption = () => {
    if (!data?.error_distribution) return {};
    const centers = data.error_distribution.map((b) => `${b.bin_center} MW`);
    const counts = data.error_distribution.map((b) => b.count);

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
          const b = data.error_distribution[idx];
          return `
            <div class="text-xs">
              <div class="font-mono font-semibold text-teal-300">Bin: [${b.bin_min} to ${b.bin_max} MW]</div>
              <div class="text-slate-300 mt-1">Count: <strong>${b.count}</strong> intervals</div>
            </div>
          `;
        },
      },
      grid: { left: "3%", right: "3%", top: "12%", bottom: "12%", containLabel: true },
      xAxis: {
        type: "category",
        data: centers,
        axisLine: { lineStyle: { color: "#334155" } },
        axisLabel: { color: "#94A3B8", fontSize: 9, rotate: 45 },
      },
      yAxis: {
        type: "value",
        name: "Intervals",
        splitLine: { lineStyle: { color: "#1E293B" } },
        axisLabel: { color: "#94A3B8" },
        nameTextStyle: { color: "#94A3B8" },
      },
      series: [
        {
          name: "Frequency",
          type: "bar",
          data: counts,
          itemStyle: {
            color: "rgba(20, 184, 166, 0.65)",
            borderColor: "#14B8A6",
            borderWidth: 1,
          },
        },
      ],
    };
  };

  // Scatter Plot Option
  const getScatterOption = () => {
    if (!data?.scatter_points) return {};
    const points = data.scatter_points.map((p) => [p.actual_mw, p.forecast_mw]);

    // Compute max for 1:1 reference line
    const maxVal = Math.max(
      ...data.scatter_points.map((p) => Math.max(p.actual_mw, p.forecast_mw)),
      1000
    );

    return {
      backgroundColor: "transparent",
      tooltip: {
        trigger: "item",
        backgroundColor: "#0F172A",
        borderColor: "#334155",
        textStyle: { color: "#F8FAFC", fontSize: 12 },
        formatter: (params: any) => {
          const val = params.value;
          const err = round(val[1] - val[0], 1);
          return `
            <div class="text-xs font-mono">
              <div>Actual: <strong>${val[0].toLocaleString()} MW</strong></div>
              <div>Forecast: <strong>${val[1].toLocaleString()} MW</strong></div>
              <div class="mt-1 pt-1 border-t border-slate-700 ${err > 0 ? "text-amber-400" : "text-cyan-400"}">
                Deviation: ${err > 0 ? `+${err}` : err} MW
              </div>
            </div>
          `;
        },
      },
      grid: { left: "3%", right: "3%", top: "12%", bottom: "10%", containLabel: true },
      xAxis: {
        type: "value",
        name: "Actual Generation (MW)",
        splitLine: { lineStyle: { color: "#1E293B" } },
        axisLabel: { color: "#94A3B8" },
        nameTextStyle: { color: "#94A3B8" },
      },
      yAxis: {
        type: "value",
        name: "Forecast Generation (MW)",
        splitLine: { lineStyle: { color: "#1E293B" } },
        axisLabel: { color: "#94A3B8" },
        nameTextStyle: { color: "#94A3B8" },
      },
      series: [
        {
          name: "Observations",
          type: "scatter",
          data: points,
          symbolSize: 6,
          itemStyle: {
            color: "rgba(6, 182, 212, 0.6)",
          },
        },
        {
          name: "1:1 Perfect Forecast Line",
          type: "line",
          data: [[0, 0], [maxVal, maxVal]],
          lineStyle: { color: "#F59E0B", type: "dashed", width: 1.5 },
          symbol: "none",
        },
      ],
    };
  };

  const round = (val: number, decimals: number) => {
    return Math.round(val * Math.pow(10, decimals)) / Math.pow(10, decimals);
  };

  return (
    <div className="space-y-6">
      {/* Date Range Selection Bar */}
      <div className="card-surface p-4 rounded-xl flex flex-wrap items-center justify-between gap-4">
        <div className="flex flex-wrap items-center gap-4">
          <div className="flex items-center space-x-2">
            <Calendar className="w-4 h-4 text-teal-400" />
            <label className="text-xs font-semibold uppercase tracking-wider text-slate-400">
              Evaluation Range:
            </label>
            <select
              value={dateFrom}
              onChange={(e) => setDateFrom(e.target.value)}
              className="bg-navy-900 border border-slate-700 text-slate-100 text-xs sm:text-sm rounded-lg px-3 py-1.5 focus:outline-none focus:border-teal-500 font-mono"
            >
              {januaryDates.map((d) => (
                <option key={d} value={d}>
                  {d}
                </option>
              ))}
            </select>
            <span className="text-slate-500 text-xs">to</span>
            <select
              value={dateTo}
              onChange={(e) => setDateTo(e.target.value)}
              className="bg-navy-900 border border-slate-700 text-slate-100 text-xs sm:text-sm rounded-lg px-3 py-1.5 focus:outline-none focus:border-teal-500 font-mono"
            >
              {januaryDates.map((d) => (
                <option key={d} value={d}>
                  {d}
                </option>
              ))}
            </select>
          </div>
        </div>

        <div className="text-xs font-mono text-slate-400 flex items-center space-x-2">
          <span>Fixed Decision Cutoff:</span>
          <span className="text-emerald-400 font-semibold">{cutoffTime} UK Local</span>
        </div>
      </div>

      {isLoading && (
        <div className="card-surface p-12 rounded-xl text-center text-slate-400 animate-pulse font-mono">
          Calculating rigorous forecast accuracy metrics across {dateFrom} to {dateTo}...
        </div>
      )}

      {isError && (
        <div className="card-surface p-6 rounded-xl border-rose-500/30 bg-rose-500/10 text-rose-300 flex items-center space-x-3">
          <AlertTriangle className="w-6 h-6 text-rose-400 flex-shrink-0" />
          <div>
            <div className="font-semibold text-sm">Failed to evaluate accuracy metrics</div>
            <div className="text-xs text-rose-400/80">{(error as Error)?.message}</div>
          </div>
        </div>
      )}

      {data && (
        <>
          {/* Key Accuracy Metrics Banner */}
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
            <div className="card-surface p-4 rounded-xl">
              <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-1">
                Mean Abs Error (MAE)
              </div>
              <div className="text-2xl font-bold font-mono text-white">
                {data.mae_mw.toLocaleString()} <span className="text-xs text-slate-400">MW</span>
              </div>
              <div className="text-xs text-slate-400 mt-1">Average deviation</div>
            </div>

            <div className="card-surface p-4 rounded-xl">
              <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-1">
                RMSE
              </div>
              <div className="text-2xl font-bold font-mono text-slate-200">
                {data.rmse_mw.toLocaleString()} <span className="text-xs text-slate-400">MW</span>
              </div>
              <div className="text-xs text-slate-400 mt-1">Quadratic penalty</div>
            </div>

            <div className="card-surface p-4 rounded-xl">
              <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-1">
                WAPE %
              </div>
              <div className="text-2xl font-bold font-mono text-teal-300">
                {data.wape_percent}%
              </div>
              <div className="text-xs text-slate-400 mt-1">Weighted error rate</div>
            </div>

            <div className="card-surface p-4 rounded-xl">
              <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-1">
                Systematic Bias (MBE)
              </div>
              <div className={`text-2xl font-bold font-mono ${data.bias_mw > 0 ? "text-amber-400" : "text-cyan-400"}`}>
                {data.bias_mw > 0 ? `+${data.bias_mw}` : data.bias_mw} <span className="text-xs text-slate-400">MW</span>
              </div>
              <div className="text-xs text-slate-400 mt-1">
                {data.bias_mw > 0 ? "Overforecast tendency" : "Underforecast tendency"}
              </div>
            </div>

            <div className="card-surface p-4 rounded-xl">
              <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-1">
                Over vs Under Rate
              </div>
              <div className="text-lg font-bold font-mono text-slate-200">
                <span className="text-amber-400">{data.overforecast_rate_percent}%</span> / <span className="text-cyan-400">{data.underforecast_rate_percent}%</span>
              </div>
              <div className="text-xs text-slate-400 mt-1">
                {data.overforecast_count} Long / {data.underforecast_count} Short
              </div>
            </div>

            <div className="card-surface p-4 rounded-xl">
              <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-1">
                Matched Samples
              </div>
              <div className="text-2xl font-bold font-mono text-emerald-400">
                {data.sample_count} <span className="text-xs text-slate-400">hours</span>
              </div>
              <div className="text-xs text-slate-400 mt-1">{data.coverage_percent}% Coverage</div>
            </div>
          </div>

          {/* Quantile Percentiles Grid */}
          <div className="card-surface p-4 rounded-xl border border-slate-800">
            <div className="text-xs font-semibold text-slate-300 uppercase tracking-wider mb-3 flex items-center space-x-2">
              <Info className="w-4 h-4 text-teal-400" />
              <span>Empirical Error Quantiles (Signed Residuals in MW)</span>
            </div>
            <div className="grid grid-cols-5 gap-2 text-center font-mono">
              <div className="bg-navy-900 p-2.5 rounded-lg border border-slate-800">
                <div className="text-[10px] text-slate-400">P10 (Downside Tail)</div>
                <div className="text-sm font-bold text-amber-400 mt-0.5">{data.quantiles.p10} MW</div>
              </div>
              <div className="bg-navy-900 p-2.5 rounded-lg border border-slate-800">
                <div className="text-[10px] text-slate-400">P25 (Lower Quartile)</div>
                <div className="text-sm font-bold text-slate-300 mt-0.5">{data.quantiles.p25} MW</div>
              </div>
              <div className="bg-navy-900 p-2.5 rounded-lg border border-slate-800">
                <div className="text-[10px] text-slate-400">P50 (Median Error)</div>
                <div className="text-sm font-bold text-teal-300 mt-0.5">{data.quantiles.p50_median} MW</div>
              </div>
              <div className="bg-navy-900 p-2.5 rounded-lg border border-slate-800">
                <div className="text-[10px] text-slate-400">P75 (Upper Quartile)</div>
                <div className="text-sm font-bold text-slate-300 mt-0.5">{data.quantiles.p75} MW</div>
              </div>
              <div className="bg-navy-900 p-2.5 rounded-lg border border-slate-800">
                <div className="text-[10px] text-slate-400">P90 (Upside Tail)</div>
                <div className="text-sm font-bold text-cyan-400 mt-0.5">{data.quantiles.p90} MW</div>
              </div>
            </div>
          </div>

          {/* 2x2 Analytics Charts Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* 1. Daily Accuracy Trend */}
            <div className="card-surface p-5 rounded-xl space-y-2">
              <h3 className="text-sm font-bold text-white flex items-center space-x-2">
                <TrendingUp className="w-4 h-4 text-teal-400" />
                <span>Daily Accuracy Breakdown (MAE, RMSE & Signed Bias)</span>
              </h3>
              <p className="text-xs text-slate-400">
                Day-by-day evolution across January delivery dates
              </p>
              <div className="h-[300px]">
                <ReactECharts option={getDailyTrendOption()} style={{ height: "100%", width: "100%" }} />
              </div>
            </div>

            {/* 2. Hour-of-Day Profile */}
            <div className="card-surface p-5 rounded-xl space-y-2">
              <h3 className="text-sm font-bold text-white flex items-center space-x-2">
                <Clock className="w-4 h-4 text-cyan-400" />
                <span>Diurnal / Hour-of-Day Error Profile (00:00–23:00)</span>
              </h3>
              <p className="text-xs text-slate-400">
                Examines whether errors spike during peak ramp hours
              </p>
              <div className="h-[300px]">
                <ReactECharts option={getHourlyOption()} style={{ height: "100%", width: "100%" }} />
              </div>
            </div>

            {/* 3. Error Distribution Histogram */}
            <div className="card-surface p-5 rounded-xl space-y-2">
              <h3 className="text-sm font-bold text-white flex items-center space-x-2">
                <BarChart3 className="w-4 h-4 text-emerald-400" />
                <span>Residual Forecast Error Distribution (MW)</span>
              </h3>
              <p className="text-xs text-slate-400">
                Histogram of signed deviations (Forecast minus Actual)
              </p>
              <div className="h-[300px]">
                <ReactECharts option={getHistogramOption()} style={{ height: "100%", width: "100%" }} />
              </div>
            </div>

            {/* 4. Forecast vs Actual Scatter */}
            <div className="card-surface p-5 rounded-xl space-y-2">
              <h3 className="text-sm font-bold text-white flex items-center space-x-2">
                <ScatterChart className="w-4 h-4 text-amber-400" />
                <span>Forecast vs Actual Outturn Scatter Plot</span>
              </h3>
              <p className="text-xs text-slate-400">
                Points above dashed line represent overforecasts; below are underforecasts
              </p>
              <div className="h-[300px]">
                <ReactECharts option={getScatterOption()} style={{ height: "100%", width: "100%" }} />
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
};
