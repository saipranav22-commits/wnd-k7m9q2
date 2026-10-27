from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timezone
from backend.models.database import get_db, ActualWindGeneration, ForecastWindGeneration
from backend.models.schemas import MetadataResponse
from backend.config import DEFAULT_DECISION_CUTOFF_TIME, TIMEZONE_UK

router = APIRouter(prefix="/api", tags=["Metadata"])

@router.get("/metadata", response_model=MetadataResponse)
def get_metadata(db: Session = Depends(get_db)):
    actual_count = db.query(func.count(ActualWindGeneration.id)).scalar() or 0
    forecast_count = db.query(func.count(ForecastWindGeneration.id)).scalar() or 0

    return MetadataResponse(
        product_name="AERIS — Wind Forecast Intelligence",
        subtitle="Day-Ahead Wind Generation & Forecast Accuracy",
        client_target="UK Electricity Utility Day-Ahead Trading Desk",
        decision_dates_supported="2026-01-01 to 2026-01-31",
        delivery_dates_supported="2026-01-02 to 2026-02-01",
        actual_dataset="Elexon BMRS FUELHH (fuelType=WIND)",
        actual_url="https://bmrs.elexon.co.uk/api-documentation/endpoint/datasets/FUELHH/stream",
        forecast_dataset="Elexon BMRS WINDFOR",
        forecast_url="https://bmrs.elexon.co.uk/api-documentation/endpoint/datasets/WINDFOR/stream",
        point_in_time_rule="publishTime <= decision_cutoff_utc",
        default_cutoff_time=DEFAULT_DECISION_CUTOFF_TIME,
        timezone=f"{TIMEZONE_UK} / UTC",
        refresh_timestamp=datetime.now(timezone.utc).isoformat(),
        total_actual_records=actual_count,
        total_forecast_records=forecast_count
    )
