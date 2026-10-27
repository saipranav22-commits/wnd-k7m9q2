from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from backend.models.database import get_db
from backend.models.schemas import DecisionExplorerResponse, DecisionPeriodItem, OverviewKPIs
from backend.services.point_in_time import PointInTimeEngine
from backend.services.accuracy_engine import AccuracyEngine
from backend.config import DEFAULT_DECISION_START_DATE, DEFAULT_DECISION_CUTOFF_TIME

router = APIRouter(prefix="/api", tags=["Decisions"])

@router.get("/decisions", response_model=DecisionExplorerResponse)
def get_decisions(
    decision_date: str = Query(DEFAULT_DECISION_START_DATE, description="Decision date YYYY-MM-DD"),
    cutoff_time: str = Query(DEFAULT_DECISION_CUTOFF_TIME, description="Cutoff time HH:MM"),
    db: Session = Depends(get_db)
):
    try:
        pit = PointInTimeEngine(db)
        acc = AccuracyEngine(db)

        res = pit.get_day_ahead_matched_data(decision_date, cutoff_time)
        half_hourly = res["half_hourly_records"]

        pairs = [
            {"forecast": r["forecast_mw"], "actual": r["actual_mw"]}
            for r in half_hourly
            if r["forecast_mw"] is not None and r["actual_mw"] is not None
        ]
        metrics = acc.calculate_metrics_for_pairs(pairs)

        total_points = len(half_hourly)
        matched_points = metrics["sample_count"]
        coverage_pct = round((matched_points / total_points * 100.0), 1) if total_points > 0 else 0.0

        p10_err = metrics["quantiles"]["p10"]
        p90_err = metrics["quantiles"]["p90"]

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

        period_items = []
        for r in half_hourly:
            f_mw = r["forecast_mw"]
            p10_band = max(0.0, round(f_mw + p10_err, 2)) if f_mw is not None else None
            p90_band = max(0.0, round(f_mw + p90_err, 2)) if f_mw is not None else None

            period_items.append(DecisionPeriodItem(
                interval_index=r["interval_index"],
                start_time_utc=r["start_time_utc"],
                start_time_local=r["start_time_local"],
                settlement_period=r["settlement_period"],
                hour=r["hour"],
                forecast_mw=f_mw,
                actual_mw=r["actual_mw"],
                forecast_publish_time_utc=r["forecast_publish_time_utc"],
                lead_time_hours=r["lead_time_hours"],
                signed_error_mw=r["signed_error_mw"],
                abs_error_mw=r["abs_error_mw"],
                lower_bound_p10_mw=p10_band,
                upper_bound_p90_mw=p90_band,
                status=r["status"],
            ))

        return DecisionExplorerResponse(
            decision_date=decision_date,
            delivery_date=res["delivery_date"],
            cutoff_time=cutoff_time,
            cutoff_datetime_utc=res["cutoff_datetime_utc"],
            kpis=kpis,
            periods=period_items,
        )

    except ValueError as ve:
        raise HTTPException(status_code=400, detail=f"Parameter error: {ve}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Decision explorer error: {e}")
