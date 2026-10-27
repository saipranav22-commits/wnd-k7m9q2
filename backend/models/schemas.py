from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class HealthResponse(BaseModel):
    status: str = "healthy"
    database_connected: bool
    actual_records_count: int
    forecast_records_count: int
    latest_actual_time: Optional[str] = None
    latest_forecast_publish_time: Optional[str] = None
    version: str = "1.0.0"

class SeriesPoint(BaseModel):
    start_time_utc: str
    start_time_local: str
    hour: int
    settlement_period: Optional[int] = None
    forecast_mw: Optional[float] = None
    actual_mw: Optional[float] = None
    error_mw: Optional[float] = None
    abs_error_mw: Optional[float] = None
    forecast_mwh: Optional[float] = None
    actual_mwh: Optional[float] = None
    publish_time_utc: Optional[str] = None
    status: str  # MATCHED, MISSING_FORECAST, MISSING_ACTUAL

class OverviewKPIs(BaseModel):
    decision_date: str
    delivery_date: str
    cutoff_time: str
    cutoff_datetime_utc: str
    total_actual_mwh: float
    total_forecast_mwh: float
    average_actual_mw: float
    average_forecast_mw: float
    mae_mw: float
    rmse_mw: float
    bias_mw: float
    wape_percent: float
    coverage_percent: float
    matched_points: int
    total_points: int
    overforecast_hours: int
    underforecast_hours: int

class OverviewResponse(BaseModel):
    kpis: OverviewKPIs
    timeseries: List[SeriesPoint]
    commentary: str

class DecisionPeriodItem(BaseModel):
    interval_index: int
    start_time_utc: str
    start_time_local: str
    settlement_period: Optional[int] = None
    hour: int
    forecast_mw: Optional[float] = None
    actual_mw: Optional[float] = None
    forecast_publish_time_utc: Optional[str] = None
    lead_time_hours: Optional[float] = None
    signed_error_mw: Optional[float] = None
    abs_error_mw: Optional[float] = None
    lower_bound_p10_mw: Optional[float] = None
    upper_bound_p90_mw: Optional[float] = None
    status: str

class DecisionExplorerResponse(BaseModel):
    decision_date: str
    delivery_date: str
    cutoff_time: str
    cutoff_datetime_utc: str
    kpis: OverviewKPIs
    periods: List[DecisionPeriodItem]

class DailyAccuracyMetric(BaseModel):
    delivery_date: str
    decision_date: str
    sample_count: int
    mae_mw: float
    rmse_mw: float
    bias_mw: float
    wape_percent: float
    actual_mwh: float
    forecast_mwh: float

class HourlyAccuracyMetric(BaseModel):
    hour: int
    sample_count: int
    mae_mw: float
    rmse_mw: float
    bias_mw: float
    actual_avg_mw: float
    forecast_avg_mw: float

class HistogramBin(BaseModel):
    bin_min: float
    bin_max: float
    bin_center: float
    count: int

class ScatterPoint(BaseModel):
    actual_mw: float
    forecast_mw: float
    error_mw: float
    start_time_utc: str

class QuantileMetrics(BaseModel):
    p10: float
    p25: float
    p50_median: float
    p75: float
    p90: float

class AccuracyResponse(BaseModel):
    date_from: str
    date_to: str
    cutoff_time: str
    sample_count: int
    coverage_percent: float
    mae_mw: float
    rmse_mw: float
    bias_mw: float
    wape_percent: float
    overforecast_count: int
    underforecast_count: int
    overforecast_rate_percent: float
    underforecast_rate_percent: float
    quantiles: QuantileMetrics
    daily_metrics: List[DailyAccuracyMetric]
    hourly_metrics: List[HourlyAccuracyMetric]
    error_distribution: List[HistogramBin]
    scatter_points: List[ScatterPoint]

class RecordItem(BaseModel):
    id: int
    delivery_date: str
    settlement_period: Optional[int]
    start_time_utc: str
    start_time_local: str
    actual_mw: Optional[float]
    forecast_mw: Optional[float]
    forecast_publish_time_utc: Optional[str]
    signed_error_mw: Optional[float]
    abs_error_mw: Optional[float]
    coverage_status: str

class RecordsResponse(BaseModel):
    total_records: int
    page: int
    page_size: int
    total_pages: int
    items: List[RecordItem]

class MetadataResponse(BaseModel):
    product_name: str = "AERIS — Wind Forecast Intelligence"
    subtitle: str = "Day-Ahead Wind Generation & Forecast Accuracy"
    client_target: str = "UK Electricity Utility Day-Ahead Trading Desk"
    decision_dates_supported: str = "2026-01-01 to 2026-01-31"
    delivery_dates_supported: str = "2026-01-02 to 2026-02-01"
    actual_dataset: str = "Elexon BMRS FUELHH (fuelType=WIND)"
    actual_url: str = "https://bmrs.elexon.co.uk/api-documentation/endpoint/datasets/FUELHH/stream"
    forecast_dataset: str = "Elexon BMRS WINDFOR"
    forecast_url: str = "https://bmrs.elexon.co.uk/api-documentation/endpoint/datasets/WINDFOR/stream"
    point_in_time_rule: str = "publishTime <= decision_cutoff_utc"
    default_cutoff_time: str = "11:00"
    timezone: str = "Europe/London / UTC"
    refresh_timestamp: str
    total_actual_records: int
    total_forecast_records: int
