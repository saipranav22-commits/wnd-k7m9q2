from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from backend.models.database import get_db
from backend.models.schemas import (
    AccuracyResponse,
    QuantileMetrics,
    DailyAccuracyMetric,
    HourlyAccuracyMetric,
    HistogramBin,
    ScatterPoint,
)
from backend.services.accuracy_engine import AccuracyEngine
from backend.config import DEFAULT_DECISION_START_DATE, DEFAULT_DECISION_END_DATE, DEFAULT_DECISION_CUTOFF_TIME

router = APIRouter(prefix="/api", tags=["Accuracy"])

@router.get("/accuracy", response_model=AccuracyResponse)
def get_accuracy(
    date_from: str = Query(DEFAULT_DECISION_START_DATE, description="Start decision date YYYY-MM-DD"),
    date_to: str = Query(DEFAULT_DECISION_END_DATE, description="End decision date YYYY-MM-DD"),
    cutoff_time: str = Query(DEFAULT_DECISION_CUTOFF_TIME, description="Cutoff time HH:MM"),
    db: Session = Depends(get_db)
):
    try:
        acc = AccuracyEngine(db)
        res = acc.evaluate_month_accuracy(date_from, date_to, cutoff_time)

        return AccuracyResponse(
            date_from=res["date_from"],
            date_to=res["date_to"],
            cutoff_time=res["cutoff_time"],
            sample_count=res["sample_count"],
            coverage_percent=res["coverage_percent"],
            mae_mw=res["mae_mw"],
            rmse_mw=res["rmse_mw"],
            bias_mw=res["bias_mw"],
            wape_percent=res["wape_percent"],
            overforecast_count=res["overforecast_count"],
            underforecast_count=res["underforecast_count"],
            overforecast_rate_percent=res["overforecast_rate_percent"],
            underforecast_rate_percent=res["underforecast_rate_percent"],
            quantiles=QuantileMetrics(**res["quantiles"]),
            daily_metrics=[DailyAccuracyMetric(**d) for d in res["daily_metrics"]],
            hourly_metrics=[HourlyAccuracyMetric(**h) for h in res["hourly_metrics"]],
            error_distribution=[HistogramBin(**b) for b in res["error_distribution"]],
            scatter_points=[ScatterPoint(**s) for s in res["scatter_points"]],
        )

    except ValueError as ve:
        raise HTTPException(status_code=400, detail=f"Invalid parameter: {ve}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Accuracy evaluation error: {e}")
