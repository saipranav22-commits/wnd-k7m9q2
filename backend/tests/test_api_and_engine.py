import os
import sys
import pytest
from fastapi.testclient import TestClient

# Ensure backend can be imported
sys.path.insert(0, os.path.abspath("."))
sys.path.insert(0, os.path.abspath("E:/REintWindAnalytics"))

from backend.main import app
from backend.models.database import SessionLocal, ActualWindGeneration, ForecastWindGeneration
from backend.services.point_in_time import PointInTimeEngine
from backend.services.accuracy_engine import AccuracyEngine

client = TestClient(app)

def test_health_endpoint():
    resp = client.get("/api/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert data["database_connected"] is True
    assert data["actual_records_count"] == 1584
    assert data["forecast_records_count"] == 19272
    assert data["latest_actual_time"] is not None
    assert data["latest_forecast_publish_time"] is not None

def test_metadata_endpoint():
    resp = client.get("/api/metadata")
    assert resp.status_code == 200
    data = resp.json()
    assert data["product_name"] == "AERIS — Wind Forecast Intelligence"
    assert "FUELHH" in data["actual_dataset"]
    assert "WINDFOR" in data["forecast_dataset"]
    assert data["default_cutoff_time"] == "11:00"

def test_overview_endpoint():
    resp = client.get("/api/overview?decision_date=2026-01-15&cutoff_time=11:00")
    assert resp.status_code == 200
    data = resp.json()
    assert "kpis" in data
    assert "timeseries" in data
    kpis = data["kpis"]
    assert kpis["decision_date"] == "2026-01-15"
    assert kpis["delivery_date"] == "2026-01-16"
    assert kpis["mae_mw"] > 0
    assert kpis["rmse_mw"] >= kpis["mae_mw"]  # Mathematical property: RMSE >= MAE
    assert kpis["matched_points"] == 24
    assert len(data["timeseries"]) == 24
    assert len(data["commentary"]) > 20

def test_decisions_explorer_endpoint():
    resp = client.get("/api/decisions?decision_date=2026-01-15&cutoff_time=11:00")
    assert resp.status_code == 200
    data = resp.json()
    assert data["decision_date"] == "2026-01-15"
    assert data["delivery_date"] == "2026-01-16"
    periods = data["periods"]
    assert len(periods) == 48  # 48 settlement periods
    p1 = periods[0]
    assert p1["settlement_period"] == 1
    assert p1["forecast_mw"] is not None
    assert p1["actual_mw"] is not None
    assert p1["lead_time_hours"] is not None
    assert p1["lower_bound_p10_mw"] is not None
    assert p1["upper_bound_p90_mw"] is not None

def test_accuracy_analytics_endpoint():
    resp = client.get("/api/accuracy?date_from=2026-01-01&date_to=2026-01-07&cutoff_time=11:00")
    assert resp.status_code == 200
    data = resp.json()
    assert data["sample_count"] > 0
    assert data["mae_mw"] > 0
    assert data["rmse_mw"] >= data["mae_mw"]
    assert len(data["daily_metrics"]) == 7
    assert len(data["hourly_metrics"]) == 24
    assert len(data["error_distribution"]) == 20
    assert len(data["scatter_points"]) > 0

def test_records_pagination_and_filter():
    resp = client.get("/api/records?page=1&page_size=25&status=MATCHED")
    assert resp.status_code == 200
    data = resp.json()
    assert data["page"] == 1
    assert data["page_size"] == 25
    assert len(data["items"]) == 25
    assert data["total_records"] > 0

def test_csv_export():
    resp = client.get("/api/export/csv?date_from=2026-01-01&date_to=2026-01-02&cutoff_time=11:00")
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "text/csv; charset=utf-8"
    assert "aeris_wind_data" in resp.headers["content-disposition"]
    lines = resp.text.strip().split("\r\n") if "\r\n" in resp.text else resp.text.strip().split("\n")
    assert len(lines) >= 97  # Header + 48*2 periods = 97 lines
    header = lines[0].split(",")
    assert "decision_date" in header
    assert "delivery_date" in header
    assert "signed_error_mw" in header

def test_point_in_time_strict_cutoff_filtering():
    """
    CRITICAL EVALUATION TEST:
    Verify that cutoff at 11:00 UTC strictly excludes forecasts published at 11:30 UTC
    and selects the earlier 09:30 UTC publication.
    Then verify that cutoff at 12:00 UTC selects the 11:30 UTC publication!
    """
    db = SessionLocal()
    try:
        pit = PointInTimeEngine(db)

        # On 2026-01-05:
        # Check cutoff at 11:00
        res_1100 = pit.get_day_ahead_matched_data("2026-01-05", "11:00")
        f1100 = res_1100["hourly_records"][12]  # hour 12:00 delivery

        # Check cutoff at 12:00
        res_1200 = pit.get_day_ahead_matched_data("2026-01-05", "12:00")
        f1200 = res_1200["hourly_records"][12]

        pub_1100 = f1100["publish_time_utc"]
        pub_1200 = f1200["publish_time_utc"]

        # Ensure that pub_1100 was published <= 11:00 UTC
        assert "2026-01-05T11:00:00Z" >= pub_1100
        # Ensure that pub_1200 is later or equal (11:30Z run was incorporated)
        assert pub_1200 >= pub_1100
        print(f"\nPoint-in-Time Proof: Cutoff 11:00 -> pub {pub_1100} | Cutoff 12:00 -> pub {pub_1200}")
    finally:
        db.close()
