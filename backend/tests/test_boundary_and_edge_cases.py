import os
import sys
import pytest
from datetime import datetime, time, timedelta
from sqlalchemy import func

sys.path.insert(0, os.path.abspath("."))
sys.path.insert(0, os.path.abspath("E:/REintWindAnalytics"))

from backend.models.database import SessionLocal, ActualWindGeneration, ForecastWindGeneration
from backend.services.point_in_time import PointInTimeEngine, parse_decision_cutoff_utc
from backend.services.accuracy_engine import AccuracyEngine
from backend.routers.records import sanitize_csv_cell

def test_deduplication_integrity():
    """Verify 0 duplicate records exist in the verified SQLite database."""
    db = SessionLocal()
    try:
        # Check actual duplicates on (start_time, fuel_type)
        act_dups = (
            db.query(ActualWindGeneration.start_time, func.count(ActualWindGeneration.id))
            .group_by(ActualWindGeneration.start_time)
            .having(func.count(ActualWindGeneration.id) > 1)
            .all()
        )
        assert len(act_dups) == 0, f"Found {len(act_dups)} duplicate actual records!"

        # Check forecast duplicates on (publish_time, start_time)
        fc_dups = (
            db.query(
                ForecastWindGeneration.publish_time,
                ForecastWindGeneration.start_time,
                func.count(ForecastWindGeneration.id)
            )
            .group_by(ForecastWindGeneration.publish_time, ForecastWindGeneration.start_time)
            .having(func.count(ForecastWindGeneration.id) > 1)
            .all()
        )
        assert len(fc_dups) == 0, f"Found {len(fc_dups)} duplicate forecast records!"
    finally:
        db.close()

def test_january_to_february_boundary():
    """
    Verify decision on January 31, 2026 targets delivery on February 1, 2026
    and contains all 48 half-hour settlement periods.
    """
    db = SessionLocal()
    try:
        pit = PointInTimeEngine(db)
        res = pit.get_day_ahead_matched_data("2026-01-31", "11:00")
        assert res["decision_date"] == "2026-01-31"
        assert res["delivery_date"] == "2026-02-01"

        half_hourly = res["half_hourly_records"]
        assert len(half_hourly) == 48

        # Verify periods 1 to 48 exist consecutively
        periods = [p["settlement_period"] for p in half_hourly]
        assert periods == list(range(1, 49))

        # Check that actuals exist for Feb 1
        matched_actuals = [p for p in half_hourly if p["actual_mw"] is not None]
        assert len(matched_actuals) == 48, "Feb 1 actuals should be 100% complete"
    finally:
        db.close()

def test_forecast_cutoff_strict_boundary():
    """
    Test exact boundary filtering:
    - Candidate with publish_time <= cutoff is accepted.
    - Candidate with publish_time > cutoff is rejected.
    """
    cutoff_utc = parse_decision_cutoff_utc("2026-01-10", "11:00")
    assert cutoff_utc.strftime("%Y-%m-%d %H:%M") == "2026-01-10 11:00"

    db = SessionLocal()
    try:
        pit = PointInTimeEngine(db)
        res_early = pit.get_day_ahead_matched_data("2026-01-10", "05:00")
        res_late = pit.get_day_ahead_matched_data("2026-01-10", "15:00")

        # Publications selected under early cutoff must be <= 05:00
        for r in res_early["hourly_records"]:
            if r["publish_time_utc"]:
                assert r["publish_time_utc"] <= "2026-01-10T05:00:00Z"

        # Late cutoff can incorporate runs up to 15:00
        for r in res_late["hourly_records"]:
            if r["publish_time_utc"]:
                assert r["publish_time_utc"] <= "2026-01-10T15:00:00Z"
    finally:
        db.close()

def test_zero_generation_and_extreme_metrics():
    """Verify metrics calculation safely handles zero generation and edge values without division by zero."""
    db = SessionLocal()
    try:
        acc = AccuracyEngine(db)

        # Case 1: Empty list
        m_empty = acc.calculate_metrics_for_pairs([])
        assert m_empty["sample_count"] == 0
        assert m_empty["wape_percent"] == 0.0
        assert m_empty["mae_mw"] == 0.0

        # Case 2: All zeroes
        zero_pairs = [{"forecast": 0.0, "actual": 0.0} for _ in range(24)]
        m_zero = acc.calculate_metrics_for_pairs(zero_pairs)
        assert m_zero["sample_count"] == 24
        assert m_zero["mae_mw"] == 0.0
        assert m_zero["rmse_mw"] == 0.0
        assert m_zero["bias_mw"] == 0.0
        assert m_zero["wape_percent"] == 0.0

        # Case 3: Forecast positive, actual zero (extreme overforecast)
        curtailment_pairs = [{"forecast": 100.0, "actual": 0.0} for _ in range(10)]
        m_curt = acc.calculate_metrics_for_pairs(curtailment_pairs)
        assert m_curt["mae_mw"] == 100.0
        assert m_curt["bias_mw"] == 100.0
        assert m_curt["overforecast_count"] == 10
        assert m_curt["underforecast_count"] == 0
        assert m_curt["wape_percent"] == 0.0  # Safe zero actuals denominator
    finally:
        db.close()

def test_missing_data_status_flags():
    """Verify that synthetic missing forecast or actual triggers proper status flag."""
    db = SessionLocal()
    try:
        pit = PointInTimeEngine(db)
        # Querying an arbitrary far-past date where no data was ingested
        res = pit.get_day_ahead_matched_data("2024-01-01", "11:00")
        for p in res["half_hourly_records"]:
            assert p["status"] in ["MISSING_FORECAST", "MISSING_BOTH", "MISSING_ACTUAL"]
            assert p["forecast_mw"] is None
            assert p["actual_mw"] is None
    finally:
        db.close()

def test_csv_formula_injection_safety():
    """Verify CSV formula injection characters (=, +, -, @) are sanitized."""
    # Dangerous formula payloads
    assert sanitize_csv_cell("=SUM(A1:A10)") == "'=SUM(A1:A10)"
    assert sanitize_csv_cell("@alert(1)") == "'@alert(1)"
    assert sanitize_csv_cell("+cmd|' /C calc'!A0") == "'+cmd|' /C calc'!A0"
    assert sanitize_csv_cell("-2+3+cmd|' /C calc'!A0") == "'-2+3+cmd|' /C calc'!A0"

    # Valid numerics should NOT be mangled
    assert sanitize_csv_cell(142.5) == 142.5
    assert sanitize_csv_cell("-142.5") == "-142.5"
    assert sanitize_csv_cell("+142.5") == "+142.5"
    assert sanitize_csv_cell(0) == 0
    assert sanitize_csv_cell(None) == ""

def test_vercel_serverless_sqlite_resolution(monkeypatch):
    """Verify that in serverless runtime (VERCEL=1), resolve_sqlite_path finds aeris.db and resolves valid path."""
    from backend.config import resolve_sqlite_path
    monkeypatch.setenv("VERCEL", "1")
    resolved = resolve_sqlite_path()
    assert resolved.exists(), f"Resolved database does not exist: {resolved}"
    assert resolved.stat().st_size > 1_000_000, f"Database is truncated: {resolved.stat().st_size} bytes"
