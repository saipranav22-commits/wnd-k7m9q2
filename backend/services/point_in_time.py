import logging
from datetime import datetime, date, time, timedelta, timezone
from typing import List, Dict, Any, Optional, Tuple
import pytz
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, desc

from backend.config import TIMEZONE_UK, DEFAULT_DECISION_CUTOFF_TIME
from backend.models.database import ActualWindGeneration, ForecastWindGeneration

logger = logging.getLogger(__name__)

def parse_decision_cutoff_utc(decision_date_str: str, cutoff_time_str: str) -> datetime:
    """
    Parse a UK-local decision date and cutoff time string into a timezone-naive UTC datetime
    for querying SQLite.
    """
    uk_tz = pytz.timezone(TIMEZONE_UK)
    d = datetime.strptime(decision_date_str, "%Y-%m-%d").date()
    t = datetime.strptime(cutoff_time_str, "%H:%M").time()
    local_dt = uk_tz.localize(datetime.combine(d, t))
    utc_dt = local_dt.astimezone(pytz.utc)
    return utc_dt.replace(tzinfo=None)

class PointInTimeEngine:
    def __init__(self, db: Session):
        self.db = db
        self.uk_tz = pytz.timezone(TIMEZONE_UK)

    def get_day_ahead_matched_data(
        self,
        decision_date_str: str,
        cutoff_time_str: str = DEFAULT_DECISION_CUTOFF_TIME
    ) -> Dict[str, Any]:
        """
        Reconstruct point-in-time forecasts and match with actuals for day-ahead delivery.
        Decision Date: D
        Delivery Date: D + 1 day
        Eligible Forecasts: publish_time <= cutoff_utc
        Selected Forecast: argmax(publish_time)
        """
        decision_date = datetime.strptime(decision_date_str, "%Y-%m-%d").date()
        delivery_date = decision_date + timedelta(days=1)
        delivery_date_str = delivery_date.strftime("%Y-%m-%d")

        cutoff_utc = parse_decision_cutoff_utc(decision_date_str, cutoff_time_str)

        # 1. Fetch all eligible forecasts published at or before cutoff targeting delivery date
        delivery_start_utc = datetime.combine(delivery_date, time(0, 0))
        delivery_end_utc = datetime.combine(delivery_date, time(23, 59, 59))

        # Query all candidate forecasts for delivery date published <= cutoff
        candidate_forecasts = (
            self.db.query(ForecastWindGeneration)
            .filter(
                ForecastWindGeneration.start_time >= delivery_start_utc,
                ForecastWindGeneration.start_time <= delivery_end_utc,
                ForecastWindGeneration.publish_time <= cutoff_utc
            )
            .order_by(ForecastWindGeneration.start_time, desc(ForecastWindGeneration.publish_time))
            .all()
        )

        # Select the latest publication for each start_time
        selected_forecasts_by_hour: Dict[datetime, ForecastWindGeneration] = {}
        for f in candidate_forecasts:
            if f.start_time not in selected_forecasts_by_hour:
                selected_forecasts_by_hour[f.start_time] = f

        # 2. Fetch actuals for the delivery date
        actuals_by_period = (
            self.db.query(ActualWindGeneration)
            .filter(ActualWindGeneration.settlement_date == delivery_date_str)
            .order_by(ActualWindGeneration.settlement_period)
            .all()
        )

        # Map actuals by settlement_period and by start_time
        actuals_map: Dict[int, ActualWindGeneration] = {a.settlement_period: a for a in actuals_by_period}

        # Build hourly aggregated structure (24 hours in delivery day)
        hourly_records: List[Dict[str, Any]] = []
        for hour in range(24):
            slot_utc = datetime.combine(delivery_date, time(hour, 0))
            slot_utc_str = slot_utc.strftime("%Y-%m-%dT%H:%M:%SZ")

            # UK local time
            slot_local = pytz.utc.localize(slot_utc).astimezone(self.uk_tz)
            slot_local_str = slot_local.strftime("%Y-%m-%d %H:%M")

            # Corresponding settlement periods (Period 1 = 00:00 to 00:30, Period 2 = 00:30 to 01:00, etc.)
            sp1 = hour * 2 + 1
            sp2 = hour * 2 + 2

            act1 = actuals_map.get(sp1)
            act2 = actuals_map.get(sp2)

            actual_mw: Optional[float] = None
            if act1 and act2:
                actual_mw = round((act1.generation_mw + act2.generation_mw) / 2.0, 2)
            elif act1:
                actual_mw = round(act1.generation_mw, 2)
            elif act2:
                actual_mw = round(act2.generation_mw, 2)

            forecast_rec = selected_forecasts_by_hour.get(slot_utc)
            forecast_mw = round(forecast_rec.generation_mw, 2) if forecast_rec else None
            pub_time_str = forecast_rec.publish_time.strftime("%Y-%m-%dT%H:%M:%SZ") if forecast_rec else None

            lead_hours = None
            if forecast_rec:
                lead_hours = round((slot_utc - forecast_rec.publish_time).total_seconds() / 3600.0, 2)

            status = "MATCHED"
            signed_error = None
            abs_error = None
            if forecast_mw is not None and actual_mw is not None:
                signed_error = round(forecast_mw - actual_mw, 2)
                abs_error = round(abs(signed_error), 2)
            elif forecast_mw is None and actual_mw is not None:
                status = "MISSING_FORECAST"
            elif forecast_mw is not None and actual_mw is None:
                status = "MISSING_ACTUAL"
            else:
                status = "MISSING_BOTH"

            hourly_records.append({
                "hour": hour,
                "interval_index": hour,
                "settlement_period_start": sp1,
                "settlement_period_end": sp2,
                "start_time_utc": slot_utc_str,
                "start_time_local": slot_local_str,
                "forecast_mw": forecast_mw,
                "actual_mw": actual_mw,
                "forecast_mwh": round(forecast_mw * 1.0, 2) if forecast_mw is not None else None,
                "actual_mwh": round(actual_mw * 1.0, 2) if actual_mw is not None else None,
                "publish_time_utc": pub_time_str,
                "lead_time_hours": lead_hours,
                "signed_error_mw": signed_error,
                "abs_error_mw": abs_error,
                "status": status,
            })

        # Also build granular 48 half-hourly settlement periods for the detailed table
        half_hourly_records: List[Dict[str, Any]] = []
        for period in range(1, 49):
            hour = (period - 1) // 2
            minute = 30 if (period % 2 == 0) else 0
            slot_utc = datetime.combine(delivery_date, time(hour, minute))
            slot_utc_str = slot_utc.strftime("%Y-%m-%dT%H:%M:%SZ")

            slot_local = pytz.utc.localize(slot_utc).astimezone(self.uk_tz)
            slot_local_str = slot_local.strftime("%Y-%m-%d %H:%M")

            act = actuals_map.get(period)
            actual_mw = round(act.generation_mw, 2) if act else None

            # Forecast for the hour
            hour_slot_utc = datetime.combine(delivery_date, time(hour, 0))
            forecast_rec = selected_forecasts_by_hour.get(hour_slot_utc)
            forecast_mw = round(forecast_rec.generation_mw, 2) if forecast_rec else None
            pub_time_str = forecast_rec.publish_time.strftime("%Y-%m-%dT%H:%M:%SZ") if forecast_rec else None

            lead_hours = None
            if forecast_rec:
                lead_hours = round((slot_utc - forecast_rec.publish_time).total_seconds() / 3600.0, 2)

            status = "MATCHED"
            signed_error = None
            abs_error = None
            if forecast_mw is not None and actual_mw is not None:
                signed_error = round(forecast_mw - actual_mw, 2)
                abs_error = round(abs(signed_error), 2)
            elif forecast_mw is None and actual_mw is not None:
                status = "MISSING_FORECAST"
            elif forecast_mw is not None and actual_mw is None:
                status = "MISSING_ACTUAL"
            else:
                status = "MISSING_BOTH"

            half_hourly_records.append({
                "settlement_period": period,
                "interval_index": period,
                "hour": hour,
                "start_time_utc": slot_utc_str,
                "start_time_local": slot_local_str,
                "forecast_mw": forecast_mw,
                "actual_mw": actual_mw,
                "forecast_mwh": round(forecast_mw * 0.5, 2) if forecast_mw is not None else None,
                "actual_mwh": round(actual_mw * 0.5, 2) if actual_mw is not None else None,
                "forecast_publish_time_utc": pub_time_str,
                "lead_time_hours": lead_hours,
                "signed_error_mw": signed_error,
                "abs_error_mw": abs_error,
                "status": status,
            })

        return {
            "decision_date": decision_date_str,
            "delivery_date": delivery_date_str,
            "cutoff_time": cutoff_time_str,
            "cutoff_datetime_utc": cutoff_utc.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "hourly_records": hourly_records,
            "half_hourly_records": half_hourly_records,
        }
