import React, { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { fetchRecords, getExportCsvUrl, RecordsResponse } from "../api/client";
import { Search, Download, ChevronLeft, ChevronRight, AlertCircle } from "lucide-react";

interface DataExplorerProps {
  cutoffTime: string;
}

export const DataExplorer: React.FC<DataExplorerProps> = ({ cutoffTime }) => {
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(50);
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("");
  const [selectedDate, setSelectedDate] = useState("");

  const { data, isLoading, isError, error } = useQuery<RecordsResponse>({
    queryKey: ["records", selectedDate, cutoffTime, status, search, page, pageSize],
    queryFn: () =>
      fetchRecords({
        decision_date: selectedDate || undefined,
        cutoff_time: cutoffTime,
        status: status || undefined,
        search: search || undefined,
        page,
        page_size: pageSize,
      }),
  });

  const januaryDates = Array.from({ length: 31 }, (_, i) => {
    const day = (i + 1).toString().padStart(2, "0");
    return `2026-01-${day}`;
  });

  const handleDownloadCsv = () => {
    const url = getExportCsvUrl("2026-01-01", "2026-01-31", cutoffTime);
    window.open(url, "_blank");
  };

  return (
    <div className="space-y-6">
      {/* Search and Filter Controls */}
      <div className="card-surface p-4 rounded-xl flex flex-wrap items-center justify-between gap-4">
        <div className="flex flex-wrap items-center gap-3">
          {/* Text Search */}
          <div className="relative">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search date, time, SP..."
              value={search}
              onChange={(e) => {
                setSearch(e.target.value);
                setPage(1);
              }}
              className="bg-navy-900 border border-slate-700 text-slate-100 text-xs sm:text-sm rounded-lg pl-9 pr-3 py-1.5 focus:outline-none focus:border-teal-500 font-mono w-48 sm:w-64"
            />
          </div>

          {/* Date Filter */}
          <select
            value={selectedDate}
            onChange={(e) => {
              setSelectedDate(e.target.value);
              setPage(1);
            }}
            className="bg-navy-900 border border-slate-700 text-slate-100 text-xs sm:text-sm rounded-lg px-3 py-1.5 focus:outline-none focus:border-teal-500 font-mono"
          >
            <option value="">All January 2026 Dates</option>
            {januaryDates.map((d) => (
              <option key={d} value={d}>
                Decision: {d}
              </option>
            ))}
          </select>

          {/* Status Filter */}
          <select
            value={status}
            onChange={(e) => {
              setStatus(e.target.value);
              setPage(1);
            }}
            className="bg-navy-900 border border-slate-700 text-slate-100 text-xs sm:text-sm rounded-lg px-3 py-1.5 focus:outline-none focus:border-teal-500 font-mono"
          >
            <option value="">All Statuses</option>
            <option value="MATCHED">Matched Only</option>
            <option value="MISSING_FORECAST">Missing Forecast</option>
            <option value="MISSING_ACTUAL">Missing Actual</option>
          </select>
        </div>

        {/* Export CSV Button */}
        <button
          onClick={handleDownloadCsv}
          className="flex items-center space-x-2 bg-gradient-to-r from-teal-600 to-emerald-600 hover:from-teal-500 hover:to-emerald-500 text-white text-xs sm:text-sm font-semibold px-4 py-2 rounded-lg shadow-md shadow-teal-500/10 transition-all font-mono"
        >
          <Download className="w-4 h-4" />
          <span>Export Full Month CSV</span>
        </button>
      </div>

      {isLoading && (
        <div className="card-surface p-12 rounded-xl text-center text-slate-400 animate-pulse font-mono">
          Loading historical records...
        </div>
      )}

      {isError && (
        <div className="card-surface p-6 rounded-xl border-rose-500/30 bg-rose-500/10 text-rose-300 flex items-center space-x-3">
          <AlertCircle className="w-6 h-6 text-rose-400 flex-shrink-0" />
          <div>
            <div className="font-semibold text-sm">Error loading records</div>
            <div className="text-xs text-rose-400/80">{(error as Error)?.message}</div>
          </div>
        </div>
      )}

      {data && (
        <div className="card-surface rounded-xl overflow-hidden border border-slate-800 space-y-2">
          {/* Header Info */}
          <div className="p-4 border-b border-slate-800 flex items-center justify-between text-xs font-mono text-slate-400">
            <div>
              Showing <strong className="text-white">{data.items.length}</strong> of{" "}
              <strong className="text-teal-400">{data.total_records.toLocaleString()}</strong> matched records
            </div>
            <div className="flex items-center space-x-3">
              <span>Rows per page:</span>
              <select
                value={pageSize}
                onChange={(e) => {
                  setPageSize(Number(e.target.value));
                  setPage(1);
                }}
                className="bg-navy-900 border border-slate-700 text-slate-200 text-xs rounded px-2 py-1"
              >
                <option value={25}>25</option>
                <option value={50}>50</option>
                <option value={100}>100</option>
              </select>
            </div>
          </div>

          {/* Table */}
          <div className="overflow-x-auto max-h-[620px] overflow-y-auto">
            <table className="w-full text-left text-xs font-mono">
              <thead className="bg-navy-900 sticky top-0 border-b border-slate-800 text-slate-400 text-[11px] uppercase tracking-wider">
                <tr>
                  <th className="py-2.5 px-3">#</th>
                  <th className="py-2.5 px-3">Delivery Date</th>
                  <th className="py-2.5 px-3">SP</th>
                  <th className="py-2.5 px-3">UTC Start</th>
                  <th className="py-2.5 px-3">Local Start</th>
                  <th className="py-2.5 px-3">Actual (MW)</th>
                  <th className="py-2.5 px-3">Forecast (MW)</th>
                  <th className="py-2.5 px-3">Published (UTC)</th>
                  <th className="py-2.5 px-3">Signed Err</th>
                  <th className="py-2.5 px-3">Abs Err</th>
                  <th className="py-2.5 px-3">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 text-slate-200">
                {data.items.map((r) => (
                  <tr key={r.id} className="hover:bg-slate-800/40 transition-colors">
                    <td className="py-2 px-3 text-slate-500">{r.id}</td>
                    <td className="py-2 px-3 text-teal-300 font-semibold">{r.delivery_date}</td>
                    <td className="py-2 px-3 font-bold text-teal-400">#{r.settlement_period}</td>
                    <td className="py-2 px-3 text-slate-400">{r.start_time_utc.split("T")[1].replace("Z", "")}</td>
                    <td className="py-2 px-3 text-slate-300">{r.start_time_local.split(" ")[1]}</td>
                    <td className="py-2 px-3 font-bold text-emerald-400">
                      {r.actual_mw != null ? `${r.actual_mw.toLocaleString()}` : "—"}
                    </td>
                    <td className="py-2 px-3 font-bold text-teal-300">
                      {r.forecast_mw != null ? `${r.forecast_mw.toLocaleString()}` : "—"}
                    </td>
                    <td className="py-2 px-3 text-[10px] text-slate-400">
                      {r.forecast_publish_time_utc ? r.forecast_publish_time_utc.replace("T", " ").replace("Z", "") : "—"}
                    </td>
                    <td className="py-2 px-3">
                      {r.signed_error_mw != null ? (
                        <span className={r.signed_error_mw > 0 ? "text-amber-400" : "text-cyan-400"}>
                          {r.signed_error_mw > 0 ? `+${r.signed_error_mw}` : r.signed_error_mw}
                        </span>
                      ) : (
                        "—"
                      )}
                    </td>
                    <td className="py-2 px-3 text-slate-300 font-mono">
                      {r.abs_error_mw !== null ? r.abs_error_mw : "—"}
                    </td>
                    <td className="py-2 px-3">
                      <span className={r.coverage_status === "MATCHED" ? "badge-matched" : "badge-missing"}>
                        {r.coverage_status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Pagination Controls */}
          <div className="p-4 border-t border-slate-800 flex items-center justify-between text-xs font-mono">
            <span className="text-slate-400">
              Page {data.page} of {data.total_pages}
            </span>
            <div className="flex items-center space-x-2">
              <button
                disabled={page <= 1}
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                className="px-3 py-1.5 rounded-lg bg-navy-900 border border-slate-700 text-slate-300 hover:text-white disabled:opacity-40 disabled:cursor-not-allowed flex items-center space-x-1"
              >
                <ChevronLeft className="w-3.5 h-3.5" />
                <span>Prev</span>
              </button>
              <button
                disabled={page >= data.total_pages}
                onClick={() => setPage((p) => Math.min(data.total_pages, p + 1))}
                className="px-3 py-1.5 rounded-lg bg-navy-900 border border-slate-700 text-slate-300 hover:text-white disabled:opacity-40 disabled:cursor-not-allowed flex items-center space-x-1"
              >
                <span>Next</span>
                <ChevronRight className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
