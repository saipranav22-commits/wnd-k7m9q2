// API Client for AERIS Platform

export interface HealthResponse {
  status: string;
  database_connected: boolean;
  actual_records_count: number;
  forecast_records_count: number;
  latest_actual_time?: string;
  latest_forecast_publish_time?: string;
  version: string;
}

export interface MetadataResponse {
  product_name: string;
  subtitle: string;
  client_target: string;
  decision_dates_supported: string;
  delivery_dates_supported: string;
  actual_dataset: string;
  actual_url: string;
  forecast_dataset: string;
  forecast_url: string;
  point_in_time_rule: string;
  default_cutoff_time: string;
  timezone: string;
  refresh_timestamp: string;
  total_actual_records: number;
  total_forecast_records: number;
}

export interface SeriesPoint {
  start_time_utc: string;
  start_time_local: string;
  hour: number;
  settlement_period?: number;
  forecast_mw?: number | null;
  actual_mw?: number | null;
  error_mw?: number | null;
  abs_error_mw?: number | null;
  forecast_mwh?: number | null;
  actual_mwh?: number | null;
  publish_time_utc?: string | null;
  status: string;
}

export interface OverviewKPIs {
  decision_date: string;
  delivery_date: string;
  cutoff_time: string;
  cutoff_datetime_utc: string;
  total_actual_mwh: number;
  total_forecast_mwh: number;
  average_actual_mw: number;
  average_forecast_mw: number;
  mae_mw: number;
  rmse_mw: number;
  bias_mw: number;
  wape_percent: number;
  coverage_percent: number;
  matched_points: number;
  total_points: number;
  overforecast_hours: number;
  underforecast_hours: number;
}

export interface OverviewResponse {
  kpis: OverviewKPIs;
  timeseries: SeriesPoint[];
  commentary: string;
}

export interface DecisionPeriodItem {
  interval_index: number;
  start_time_utc: string;
  start_time_local: string;
  settlement_period?: number;
  hour: number;
  forecast_mw?: number | null;
  actual_mw?: number | null;
  forecast_publish_time_utc?: string | null;
  lead_time_hours?: number | null;
  signed_error_mw?: number | null;
  abs_error_mw?: number | null;
  lower_bound_p10_mw?: number | null;
  upper_bound_p90_mw?: number | null;
  status: string;
}

export interface DecisionExplorerResponse {
  decision_date: string;
  delivery_date: string;
  cutoff_time: string;
  cutoff_datetime_utc: string;
  kpis: OverviewKPIs;
  periods: DecisionPeriodItem[];
}

export interface DailyAccuracyMetric {
  delivery_date: string;
  decision_date: string;
  sample_count: number;
  mae_mw: number;
  rmse_mw: number;
  bias_mw: number;
  wape_percent: number;
  actual_mwh: number;
  forecast_mwh: number;
}

export interface HourlyAccuracyMetric {
  hour: number;
  sample_count: number;
  mae_mw: number;
  rmse_mw: number;
  bias_mw: number;
  actual_avg_mw: number;
  forecast_avg_mw: number;
}

export interface HistogramBin {
  bin_min: number;
  bin_max: number;
  bin_center: number;
  count: number;
}

export interface ScatterPoint {
  actual_mw: number;
  forecast_mw: number;
  error_mw: number;
  start_time_utc: string;
}

export interface QuantileMetrics {
  p10: number;
  p25: number;
  p50_median: number;
  p75: number;
  p90: number;
}

export interface AccuracyResponse {
  date_from: string;
  date_to: string;
  cutoff_time: string;
  sample_count: number;
  coverage_percent: number;
  mae_mw: number;
  rmse_mw: number;
  bias_mw: number;
  wape_percent: number;
  overforecast_count: number;
  underforecast_count: number;
  overforecast_rate_percent: number;
  underforecast_rate_percent: number;
  quantiles: QuantileMetrics;
  daily_metrics: DailyAccuracyMetric[];
  hourly_metrics: HourlyAccuracyMetric[];
  error_distribution: HistogramBin[];
  scatter_points: ScatterPoint[];
}

export interface RecordItem {
  id: number;
  delivery_date: string;
  settlement_period?: number;
  start_time_utc: string;
  start_time_local: string;
  actual_mw?: number | null;
  forecast_mw?: number | null;
  forecast_publish_time_utc?: string | null;
  signed_error_mw?: number | null;
  abs_error_mw?: number | null;
  coverage_status: string;
}

export interface RecordsResponse {
  total_records: number;
  page: number;
  page_size: number;
  total_pages: number;
  items: RecordItem[];
}

const API_BASE = "";

async function handleResponse<T>(res: Response, fallbackMsg: string): Promise<T> {
  if (!res.ok) {
    let detail = "";
    try {
      const err = await res.json();
      detail = err.detail || "";
    } catch {
      // response was not JSON
    }
    throw new Error(detail ? `${fallbackMsg}: ${detail}` : `${fallbackMsg} (HTTP ${res.status})`);
  }
  return res.json();
}

export async function fetchHealth(): Promise<HealthResponse> {
  const res = await fetch(`${API_BASE}/api/health`);
  return handleResponse<HealthResponse>(res, "Health check failed");
}

export async function fetchMetadata(): Promise<MetadataResponse> {
  const res = await fetch(`${API_BASE}/api/metadata`);
  return handleResponse<MetadataResponse>(res, "Metadata fetch failed");
}

export async function fetchOverview(decisionDate: string, cutoffTime: string): Promise<OverviewResponse> {
  const params = new URLSearchParams({ decision_date: decisionDate, cutoff_time: cutoffTime });
  const res = await fetch(`${API_BASE}/api/overview?${params}`);
  return handleResponse<OverviewResponse>(res, "Overview fetch failed");
}

export async function fetchDecisions(decisionDate: string, cutoffTime: string): Promise<DecisionExplorerResponse> {
  const params = new URLSearchParams({ decision_date: decisionDate, cutoff_time: cutoffTime });
  const res = await fetch(`${API_BASE}/api/decisions?${params}`);
  return handleResponse<DecisionExplorerResponse>(res, "Decisions fetch failed");
}

export async function fetchAccuracy(dateFrom: string, dateTo: string, cutoffTime: string): Promise<AccuracyResponse> {
  const params = new URLSearchParams({ date_from: dateFrom, date_to: dateTo, cutoff_time: cutoffTime });
  const res = await fetch(`${API_BASE}/api/accuracy?${params}`);
  return handleResponse<AccuracyResponse>(res, "Accuracy fetch failed");
}

export async function fetchRecords(params: {
  decision_date?: string;
  delivery_date?: string;
  cutoff_time?: string;
  status?: string;
  search?: string;
  page?: number;
  page_size?: number;
}): Promise<RecordsResponse> {
  const q = new URLSearchParams();
  if (params.decision_date) q.set("decision_date", params.decision_date);
  if (params.delivery_date) q.set("delivery_date", params.delivery_date);
  if (params.cutoff_time) q.set("cutoff_time", params.cutoff_time);
  if (params.status) q.set("status", params.status);
  if (params.search) q.set("search", params.search);
  if (params.page) q.set("page", params.page.toString());
  if (params.page_size) q.set("page_size", params.page_size.toString());

  const res = await fetch(`${API_BASE}/api/records?${q}`);
  return handleResponse<RecordsResponse>(res, "Records fetch failed");
}

export function getExportCsvUrl(dateFrom: string, dateTo: string, cutoffTime: string): string {
  const q = new URLSearchParams({ date_from: dateFrom, date_to: dateTo, cutoff_time: cutoffTime });
  return `${API_BASE}/api/export/csv?${q}`;
}
