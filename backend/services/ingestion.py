import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List
from dateutil import parser as date_parser
from sqlalchemy.orm import Session
from sqlalchemy.dialects.sqlite import insert

from backend.models.database import (
    ActualWindGeneration,
    ForecastWindGeneration,
    IngestionLog,
    SessionLocal,
    init_db,
)
from backend.services.elexon_client import ElexonClient

logger = logging.getLogger(__name__)

def parse_utc_dt(val: Any) -> datetime:
    if isinstance(val, datetime):
        if val.tzinfo is None:
            return val.replace(tzinfo=timezone.utc)
        return val.astimezone(timezone.utc)
    dt = date_parser.parse(str(val))
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)

class IngestionService:
    def __init__(self, db: Session = None):
        self.db = db or SessionLocal()
        self.client = ElexonClient()

    def ingest_fuelhh_records(self, raw_records: List[Dict[str, Any]]) -> int:
        """
        Deduplicate and insert FUELHH actuals into SQLite.
        """
        if not raw_records:
            return 0

        inserted_count = 0
        for item in raw_records:
            if item.get("fuelType") != "WIND":
                continue

            try:
                start_dt = parse_utc_dt(item["startTime"]).replace(tzinfo=None)
                settlement_date = item.get("settlementDate") or start_dt.strftime("%Y-%m-%d")
                settlement_period = int(item.get("settlementPeriod", 1))
                generation_mw = float(item.get("generation", 0.0))
                publish_dt = parse_utc_dt(item["publishTime"]).replace(tzinfo=None) if item.get("publishTime") else None

                stmt = insert(ActualWindGeneration).values(
                    start_time=start_dt,
                    settlement_date=settlement_date,
                    settlement_period=settlement_period,
                    generation_mw=generation_mw,
                    fuel_type="WIND",
                    publish_time=publish_dt,
                ).on_conflict_do_update(
                    index_elements=["start_time", "fuel_type"],
                    set_={"generation_mw": generation_mw, "publish_time": publish_dt}
                )
                self.db.execute(stmt)
                inserted_count += 1
            except Exception as e:
                logger.warning(f"Skipping malformed FUELHH record {item}: {e}")

        self.db.commit()
        return inserted_count

    def ingest_windfor_records(self, raw_records: List[Dict[str, Any]]) -> int:
        """
        Deduplicate and insert WINDFOR forecasts into SQLite.
        """
        if not raw_records:
            return 0

        inserted_count = 0
        for item in raw_records:
            try:
                pub_dt = parse_utc_dt(item["publishTime"]).replace(tzinfo=None)
                start_dt = parse_utc_dt(item["startTime"]).replace(tzinfo=None)
                generation_mw = float(item.get("generation", 0.0))

                stmt = insert(ForecastWindGeneration).values(
                    publish_time=pub_dt,
                    start_time=start_dt,
                    generation_mw=generation_mw,
                    dataset="WINDFOR",
                ).on_conflict_do_update(
                    index_elements=["publish_time", "start_time"],
                    set_={"generation_mw": generation_mw}
                )
                self.db.execute(stmt)
                inserted_count += 1
            except Exception as e:
                logger.warning(f"Skipping malformed WINDFOR record {item}: {e}")

        self.db.commit()
        return inserted_count

    async def run_full_january_sync(self) -> Dict[str, Any]:
        """
        Idempotent full historical synchronization of January 2026 data.
        - FUELHH: 2026-01-01 to 2026-02-02
        - WINDFOR: 2025-12-31 to 2026-02-02 (chunked)
        """
        init_db()
        results = {"actuals_count": 0, "forecasts_count": 0, "errors": []}

        # 1. Ingest FUELHH
        try:
            actual_records = await self.client.fetch_fuelhh_actuals("2026-01-01", "2026-02-02", "WIND")
            count = self.ingest_fuelhh_records(actual_records)
            results["actuals_count"] = count
            log = IngestionLog(
                dataset_name="FUELHH",
                status="SUCCESS",
                records_ingested=count,
                start_range="2026-01-01",
                end_range="2026-02-02",
                message=f"Ingested {count} WIND records successfully."
            )
            self.db.add(log)
            self.db.commit()
            logger.info(f"Successfully synced {count} FUELHH records.")
        except Exception as e:
            msg = f"FUELHH ingestion error: {e}"
            logger.error(msg)
            results["errors"].append(msg)
            log = IngestionLog(dataset_name="FUELHH", status="FAILED", message=str(e))
            self.db.add(log)
            self.db.commit()

        # 2. Ingest WINDFOR in 4-day chunks to ensure zero timeouts
        chunk_start = datetime(2025, 12, 31, 0, 0, tzinfo=timezone.utc)
        chunk_end_limit = datetime(2026, 2, 2, 0, 0, tzinfo=timezone.utc)
        step_days = 4

        current_start = chunk_start
        total_forecasts = 0
        while current_start < chunk_end_limit:
            current_end = min(current_start + timedelta(days=step_days), chunk_end_limit)
            from_str = current_start.strftime("%Y-%m-%dT%H:%M:%SZ")
            to_str = current_end.strftime("%Y-%m-%dT%H:%M:%SZ")

            try:
                forecast_records = await self.client.fetch_windfor_forecasts(from_str, to_str)
                count = self.ingest_windfor_records(forecast_records)
                total_forecasts += count
                logger.info(f"Ingested {count} WINDFOR records for {from_str} to {to_str}")
            except Exception as e:
                msg = f"WINDFOR ingestion chunk error ({from_str} to {to_str}): {e}"
                logger.error(msg)
                results["errors"].append(msg)

            current_start = current_end
            await asyncio.sleep(0.2)  # courteous API spacing

        results["forecasts_count"] = total_forecasts
        log = IngestionLog(
            dataset_name="WINDFOR",
            status="SUCCESS" if not results["errors"] else "PARTIAL",
            records_ingested=total_forecasts,
            start_range="2025-12-31T00:00:00Z",
            end_range="2026-02-02T00:00:00Z",
            message=f"Ingested {total_forecasts} WINDFOR records."
        )
        self.db.add(log)
        self.db.commit()

        return results

    def close(self):
        self.db.close()
