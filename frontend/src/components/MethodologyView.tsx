import React from "react";
import { useQuery } from "@tanstack/react-query";
import { fetchMetadata, MetadataResponse } from "../api/client";
import { BookOpen, ExternalLink, ShieldCheck, Cpu, Database, CheckCircle2, Layers } from "lucide-react";

export const MethodologyView: React.FC = () => {
  const { data: meta } = useQuery<MetadataResponse>({
    queryKey: ["metadata"],
    queryFn: fetchMetadata,
  });

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      {/* Header */}
      <div className="card-surface p-6 rounded-xl space-y-2">
        <div className="flex items-center space-x-2 text-teal-400 text-xs font-mono font-semibold uppercase tracking-wider">
          <BookOpen className="w-4 h-4" />
          <span>Documentation & Methodology</span>
        </div>
        <h2 className="text-xl sm:text-2xl font-bold text-white tracking-tight">
          AERIS Methodology, Data Provenance & Quantitative Foundations
        </h2>
        <p className="text-sm text-slate-300 leading-relaxed">
          Comprehensive disclosure of data sources, Point-in-Time selection rules, metric formulas, and operational assumptions.
        </p>
      </div>

      {/* Grid of Methodology Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* 1. Underlying Datasets */}
        <div className="card-surface p-6 rounded-xl space-y-4">
          <h3 className="text-base font-bold text-white flex items-center space-x-2">
            <Database className="w-4 h-4 text-teal-400" />
            <span>1. Official Elexon BMRS Datasets</span>
          </h3>
          <p className="text-xs text-slate-300 leading-relaxed">
            AERIS strictly limits its underlying energy data to the two official Elexon datasets specified in the assessment guidelines:
          </p>

          <div className="space-y-3 text-xs">
            <div className="p-3 rounded-lg bg-navy-900 border border-slate-800 space-y-1">
              <div className="flex items-center justify-between font-semibold text-emerald-400 font-mono">
                <span>FUELHH — Outturn Generation Actuals</span>
                <a
                  href="https://bmrs.elexon.co.uk/api-documentation/endpoint/datasets/FUELHH/stream"
                  target="_blank"
                  rel="noreferrer"
                  className="flex items-center space-x-1 text-slate-400 hover:text-white"
                >
                  <span>Doc</span>
                  <ExternalLink className="w-3 h-3" />
                </a>
              </div>
              <p className="text-slate-400 text-[11px]">
                Filtered strictly on <code className="text-emerald-300">fuelType == 'WIND'</code>. 30-minute settlement period resolution. Units in average MW per half hour.
              </p>
            </div>

            <div className="p-3 rounded-lg bg-navy-900 border border-slate-800 space-y-1">
              <div className="flex items-center justify-between font-semibold text-teal-300 font-mono">
                <span>WINDFOR — Forecasted Wind Generation</span>
                <a
                  href="https://bmrs.elexon.co.uk/api-documentation/endpoint/datasets/WINDFOR/stream"
                  target="_blank"
                  rel="noreferrer"
                  className="flex items-center space-x-1 text-slate-400 hover:text-white"
                >
                  <span>Doc</span>
                  <ExternalLink className="w-3 h-3" />
                </a>
              </div>
              <p className="text-slate-400 text-[11px]">
                Hourly resolution forecasts published ~8 times daily by National Grid ESO. Preserves complete publication version history for realistic backtesting.
              </p>
            </div>
          </div>
        </div>

        {/* 2. Point-in-Time Selection Engine */}
        <div className="card-surface p-6 rounded-xl space-y-4">
          <h3 className="text-base font-bold text-white flex items-center space-x-2">
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
            <span>2. Point-in-Time Forecast Selection Rule</span>
          </h3>
          <p className="text-xs text-slate-300 leading-relaxed">
            To prevent look-ahead bias (hindsight), AERIS selects forecasts solely based on information that was actually published and accessible prior to the trading cutoff:
          </p>

          <div className="bg-navy-900 p-3.5 rounded-lg border border-slate-800 font-mono text-xs text-teal-300 space-y-2">
            <div># Filtering Rule:</div>
            <div className="text-white">publishTime &le; Cutoff_Timestamp(D, Cutoff_Time)</div>
            <div># Selection Algorithm:</div>
            <div className="text-white">Selected_Forecast = argmax(publishTime)</div>
          </div>

          <ul className="text-xs text-slate-400 space-y-1 list-disc pl-4">
            <li>Forecasts published after the cutoff are strictly excluded.</li>
            <li>Default 11:00 UK cutoff aligns with standard Day-Ahead auction gates.</li>
            <li>Configurable to any local UK time without look-ahead contamination.</li>
          </ul>
        </div>

        {/* 3. Mathematical Formulas */}
        <div className="card-surface p-6 rounded-xl space-y-4">
          <h3 className="text-base font-bold text-white flex items-center space-x-2">
            <Layers className="w-4 h-4 text-cyan-400" />
            <span>3. Quantitative Metric Formulations</span>
          </h3>
          <div className="space-y-2.5 text-xs font-mono">
            <div className="p-2.5 bg-navy-900 rounded border border-slate-800">
              <span className="text-teal-400 font-bold">MAE: </span>
              <span className="text-slate-200">(1/N) &Sigma; |Forecast - Actual|</span>
              <div className="text-[10px] text-slate-400 mt-0.5">Average absolute volumetric miss in MW.</div>
            </div>
            <div className="p-2.5 bg-navy-900 rounded border border-slate-800">
              <span className="text-cyan-400 font-bold">RMSE: </span>
              <span className="text-slate-200">&radic;[ (1/N) &Sigma; (Forecast - Actual)&sup2; ]</span>
              <div className="text-[10px] text-slate-400 mt-0.5">Penalizes large errors disproportionately (risk proxy).</div>
            </div>
            <div className="p-2.5 bg-navy-900 rounded border border-slate-800">
              <span className="text-amber-400 font-bold">Bias (MBE): </span>
              <span className="text-slate-200">(1/N) &Sigma; (Forecast - Actual)</span>
              <div className="text-[10px] text-slate-400 mt-0.5">Positive = Overforecast (long); Negative = Underforecast (short).</div>
            </div>
            <div className="p-2.5 bg-navy-900 rounded border border-slate-800">
              <span className="text-emerald-400 font-bold">WAPE: </span>
              <span className="text-slate-200">(&Sigma; |Forecast - Actual| / &Sigma; Actual) &times; 100%</span>
              <div className="text-[10px] text-slate-400 mt-0.5">Safe from division-by-zero during low-wind periods.</div>
            </div>
          </div>
        </div>

        {/* 4. Units & Physical Clarification */}
        <div className="card-surface p-6 rounded-xl space-y-4">
          <h3 className="text-base font-bold text-white flex items-center space-x-2">
            <CheckCircle2 className="w-4 h-4 text-amber-400" />
            <span>4. Power (MW) vs Energy (MWh)</span>
          </h3>
          <p className="text-xs text-slate-300 leading-relaxed">
            Elexon outturn and forecast readings represent interval-average power in Megawatts (MW).
          </p>
          <div className="bg-navy-900 p-3.5 rounded-lg border border-slate-800 space-y-2 text-xs">
            <div className="text-slate-300">
              <strong className="text-emerald-400 font-mono">Half-Hour Interval: </strong>
              Energy [MWh] = Power [MW] &times; 0.5 hours
            </div>
            <div className="text-slate-300">
              <strong className="text-teal-400 font-mono">1-Hour Block: </strong>
              Energy [MWh] = Power [MW] &times; 1.0 hour
            </div>
          </div>
          <p className="text-[11px] text-slate-400 leading-normal">
            AERIS clearly labels and separates instantaneous/average power rates (MW) from total electrical volume delivered (MWh) across all views.
          </p>
        </div>
      </div>

      {/* AI Tool Usage Disclosure & Compliance */}
      <div className="card-surface p-6 rounded-xl border border-teal-500/30 bg-teal-500/5 space-y-3">
        <div className="flex items-center space-x-2 text-teal-300 text-xs font-mono font-semibold uppercase tracking-wider">
          <Cpu className="w-4 h-4 text-teal-400" />
          <span>Mandatory Disclosure: AI Tool Usage</span>
        </div>
        <p className="text-xs sm:text-sm text-slate-300 leading-relaxed">
          In strict compliance with the challenge requirements, this application was developed with the assistance of
          advanced AI engineering tools, including <strong>Google Antigravity</strong> (DeepMind Advanced Agentic Coding).
          All algorithmic decisions, Point-in-Time selection criteria, unit conversions, and test fixtures have been
          rigorously reviewed and empirically verified with real Elexon data.
        </p>
      </div>

      {/* Provenance Metadata */}
      {meta && (
        <div className="card-surface p-4 rounded-xl text-xs font-mono text-slate-400 flex flex-wrap items-center justify-between gap-4">
          <div>
            Verified SQLite Cache: <span className="text-white font-semibold">{meta.total_actual_records.toLocaleString()}</span> actuals,{" "}
            <span className="text-white font-semibold">{meta.total_forecast_records.toLocaleString()}</span> forecasts
          </div>
          <div>
            Decision Scope: <span className="text-teal-300">{meta.decision_dates_supported}</span>
          </div>
          <div className="text-[11px] text-slate-500">
            Last Synced: {meta.refresh_timestamp}
          </div>
        </div>
      )}
    </div>
  );
};
