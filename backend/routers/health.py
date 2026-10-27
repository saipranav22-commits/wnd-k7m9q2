from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.models.database import get_db, ActualWindGeneration, ForecastWindGeneration
from backend.models.schemas import HealthResponse

router = APIRouter(prefix="/api", tags=["Health"])

@router.get("/health", response_model=HealthResponse)
def get_health(db: Session = Depends(get_db)):
    try:
        actual_count = db.query(func.count(ActualWindGeneration.id)).scalar() or 0
        forecast_count = db.query(func.count(ForecastWindGeneration.id)).scalar() or 0

        latest_actual = db.query(func.max(ActualWindGeneration.start_time)).scalar()
        latest_forecast = db.query(func.max(ForecastWindGeneration.publish_time)).scalar()

        return HealthResponse(
            status="healthy",
            database_connected=True,
            actual_records_count=actual_count,
            forecast_records_count=forecast_count,
            latest_actual_time=latest_actual.isoformat() if latest_actual else None,
            latest_forecast_publish_time=latest_forecast.isoformat() if latest_forecast else None,
            version="1.0.0"
        )
    except Exception as e:
        return HealthResponse(
            status="unhealthy",
            database_connected=False,
            actual_records_count=0,
            forecast_records_count=0,
            latest_actual_time=None,
            latest_forecast_publish_time=None,
            version="1.0.0"
        )
