import csv
import io
from datetime import datetime, timedelta
from typing import Optional, Any
from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session

from backend.models.database import get_db
from backend.models.schemas import RecordsResponse, RecordItem
from backend.services.point_in_time import PointInTimeEngine
from backend.config import DEFAULT_DECISION_START_DATE, DEFAULT_DECISION_END_DATE, DEFAULT_DECISION_CUTOFF_TIME

router = APIRouter(prefix="/api", tags=["Records & Export"])

@router.get("/records", response_model=RecordsResponse)
def get_records(
    decision_date: Optional[str] = Query(None, description="Optional filter by decision date YYYY-MM-DD"),
    delivery_date: Optional[str] = Query(None, description="Optional filter by delivery date YYYY-MM-DD"),
    cutoff_time: str = Query(DEFAULT_DECISION_CUTOFF_TIME, description="Cutoff time HH:MM"),
    status: Optional[str] = Query(None, description="Filter by status (MATCHED, MISSING_FORECAST, MISSING_ACTUAL)"),
    search: Optional[str] = Query(None, description="Search term in timestamps or dates"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db)
):
    try:
        pit = PointInTimeEngine(db)

        # Determine date range to collect
        if decision_date:
            dates = [decision_date]
        elif delivery_date:
            d_del = datetime.strptime(delivery_date, "%Y-%m-%d").date()
            d_dec = d_del - timedelta(days=1)
            dates = [d_dec.strftime("%Y-%m-%d")]
        else:
            # Default to full January decision dates
            d_start = datetime.strptime(DEFAULT_DECISION_START_DATE, "%Y-%m-%d").date()
            d_end = datetime.strptime(DEFAULT_DECISION_END_DATE, "%Y-%m-%d").date()
            dates = [(d_start + timedelta(days=i)).strftime("%Y-%m-%d") for i in range((d_end - d_start).days + 1)]

        all_items = []
        rec_id = 1
        for d in dates:
            data = pit.get_day_ahead_matched_data(d, cutoff_time)
            for r in data["half_hourly_records"]:
                item = RecordItem(
                    id=rec_id,
                    delivery_date=data["delivery_date"],
                    settlement_period=r["settlement_period"],
                    start_time_utc=r["start_time_utc"],
                    start_time_local=r["start_time_local"],
                    actual_mw=r["actual_mw"],
                    forecast_mw=r["forecast_mw"],
                    forecast_publish_time_utc=r["forecast_publish_time_utc"],
                    signed_error_mw=r["signed_error_mw"],
                    abs_error_mw=r["abs_error_mw"],
                    coverage_status=r["status"],
                )
                rec_id += 1

                # Filter by status
                if status and item.coverage_status != status:
                    continue

                # Filter by search term
                if search:
                    s_lower = search.lower()
                    if (s_lower not in item.delivery_date.lower() and
                        s_lower not in item.start_time_utc.lower() and
                        s_lower not in item.start_time_local.lower() and
                        s_lower not in str(item.settlement_period)):
                        continue

                all_items.append(item)

        total_records = len(all_items)
        total_pages = max(1, (total_records + page_size - 1) // page_size)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_items = all_items[start_idx:end_idx]

        return RecordsResponse(
            total_records=total_records,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            items=paginated_items,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching records: {e}")

def sanitize_csv_cell(value: Any) -> Any:
    """
    Sanitize values against CSV formula injection (CWE-1236).
    If a non-numeric string starts with '=', '+', '-', '@', '\t', or '\r',
    prefix with a single quote.
    """
    if value is None:
        return ""
    if isinstance(value, (int, float)):
        return value
    s = str(value).strip()
    try:
        float(s)
        return s
    except ValueError:
        pass
    if s.startswith(("=", "+", "-", "@", "\t", "\r")):
        return f"'{s}"
    return s

@router.get("/export/csv")
def export_csv(
    date_from: str = Query(DEFAULT_DECISION_START_DATE, description="Start decision date YYYY-MM-DD"),
    date_to: str = Query(DEFAULT_DECISION_END_DATE, description="End decision date YYYY-MM-DD"),
    cutoff_time: str = Query(DEFAULT_DECISION_CUTOFF_TIME, description="Cutoff time HH:MM"),
    db: Session = Depends(get_db)
):
    try:
        pit = PointInTimeEngine(db)
        d_start = datetime.strptime(date_from, "%Y-%m-%d").date()
        d_end = datetime.strptime(date_to, "%Y-%m-%d").date()

        output = io.StringIO()
        writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)
        writer.writerow([
            "decision_date",
            "delivery_date",
            "settlement_period",
            "start_time_utc",
            "start_time_local",
            "actual_mw",
            "forecast_mw",
            "forecast_publish_time_utc",
            "lead_time_hours",
            "signed_error_mw",
            "abs_error_mw",
            "coverage_status",
        ])

        curr = d_start
        while curr <= d_end:
            d_str = curr.strftime("%Y-%m-%d")
            data = pit.get_day_ahead_matched_data(d_str, cutoff_time)
            for r in data["half_hourly_records"]:
                writer.writerow([
                    sanitize_csv_cell(d_str),
                    sanitize_csv_cell(data["delivery_date"]),
                    sanitize_csv_cell(r["settlement_period"]),
                    sanitize_csv_cell(r["start_time_utc"]),
                    sanitize_csv_cell(r["start_time_local"]),
                    sanitize_csv_cell(r["actual_mw"]),
                    sanitize_csv_cell(r["forecast_mw"]),
                    sanitize_csv_cell(r["forecast_publish_time_utc"]),
                    sanitize_csv_cell(r["lead_time_hours"]),
                    sanitize_csv_cell(r["signed_error_mw"]),
                    sanitize_csv_cell(r["abs_error_mw"]),
                    sanitize_csv_cell(r["status"]),
                ])
            curr += timedelta(days=1)

        csv_content = output.getvalue()
        filename = f"aeris_wind_data_{date_from}_to_{date_to}_cutoff_{cutoff_time.replace(':', '')}.csv"
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error exporting CSV: {e}")
