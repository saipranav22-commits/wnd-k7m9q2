from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from backend.models.database import get_db
from backend.models.schemas import OverviewResponse, OverviewKPIs, SeriesPoint
from backend.services.point_in_time import PointInTimeEngine
from backend.services.accuracy_engine import AccuracyEngine
from backend.config import DEFAULT_DECISION_START_DATE, DEFAULT_DECISION_CUTOFF_TIME

router = APIRouter(prefix="/api", tags=["Overview"])

@router.get("/overview", response_model=OverviewResponse)
def get_overview(
    decision_date: str = Query(DEFAULT_DECISION_START_DATE, description="Decision date in YYYY-MM-DD (2026-01-01 to 2026-01-31)"),
    cutoff_time: str = Query(DEFAULT_DECISION_CUTOFF_TIME, description="Cutoff time HH:MM UK local time"),
    db: Session = Depends(get_db)
):
    try:
        pit = PointInTimeEngine(db)
        acc = AccuracyEngine(db)

        res = pit.get_day_ahead_matched_data(decision_date, cutoff_time)
        hourly_records = res["hourly_records"]

        pairs = [
            {"forecast": r["forecast_mw"], "actual": r["actual_mw"]}
            for r in hourly_records
            if r["forecast_mw"] is not None and r["actual_mw"] is not None
        ]

        metrics = acc.calculate_metrics_for_pairs(pairs)
        total_points = len(hourly_records)
        matched_points = metrics["sample_count"]
        coverage_pct = round((matched_points / total_points * 100.0), 1) if total_points > 0 else 0.0

        kpis = OverviewKPIs(
            decision_date=decision_date,
            delivery_date=res["delivery_date"],
            cutoff_time=cutoff_time,
            cutoff_datetime_utc=res["cutoff_datetime_utc"],
            total_actual_mwh=metrics["total_actual_mwh"],
            total_forecast_mwh=metrics["total_forecast_mwh"],
            average_actual_mw=metrics["average_actual_mw"],
            average_forecast_mw=metrics["average_forecast_mw"],
            mae_mw=metrics["mae_mw"],
            rmse_mw=metrics["rmse_mw"],
            bias_mw=metrics["bias_mw"],
            wape_percent=metrics["wape_percent"],
            coverage_percent=coverage_pct,
            matched_points=matched_points,
            total_points=total_points,
            overforecast_hours=metrics["overforecast_count"],
            underforecast_hours=metrics["underforecast_count"],
        )

        timeseries = [
            SeriesPoint(
                start_time_utc=r["start_time_utc"],
                start_time_local=r["start_time_local"],
                hour=r["hour"],
                settlement_period=r["settlement_period_start"],
                forecast_mw=r["forecast_mw"],
                actual_mw=r["actual_mw"],
                error_mw=r["signed_error_mw"],
                abs_error_mw=r["abs_error_mw"],
                forecast_mwh=r["forecast_mwh"],
                actual_mwh=r["actual_mwh"],
                publish_time_utc=r["publish_time_utc"],
                status=r["status"],
            )
            for r in hourly_records
        ]

        commentary = acc.generate_commentary(metrics, res["delivery_date"])

        return OverviewResponse(
            kpis=kpis,
            timeseries=timeseries,
            commentary=commentary,
        )

    except ValueError as ve:
        raise HTTPException(status_code=400, detail=f"Invalid date or time parameter: {ve}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating overview: {e}")
