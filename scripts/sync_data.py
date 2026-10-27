import asyncio
import logging
import sys
import time

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

import os
import sys

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath("."))
sys.path.insert(0, os.path.abspath("E:/REintWindAnalytics"))

from sqlalchemy import func
from backend.services.ingestion import IngestionService
from backend.models.database import SessionLocal, ActualWindGeneration, ForecastWindGeneration

async def main():
    print("=" * 60)
    print("AERIS — Historical Ingestion Pipeline: January 2026")
    print("=" * 60)

    start_time = time.time()
    service = IngestionService()
    try:
        results = await service.run_full_january_sync()
        duration = round(time.time() - start_time, 2)
        print("\n" + "=" * 60)
        print(f"Ingestion completed in {duration} seconds.")
        print(f"Actuals (FUELHH WIND) ingested: {results['actuals_count']}")
        print(f"Forecasts (WINDFOR) ingested:   {results['forecasts_count']}")
        if results["errors"]:
            print(f"Errors encountered: {results['errors']}")
        print("=" * 60)

        # Verify DB counts
        db = SessionLocal()
        try:
            act_total = db.query(func.count(ActualWindGeneration.id)).scalar()
            fc_total = db.query(func.count(ForecastWindGeneration.id)).scalar()
            print(f"\nVerification in SQLite database:")
            print(f"  Total Actual Wind Records:     {act_total}")
            print(f"  Total Forecast Wind Records:   {fc_total}")
        finally:
            db.close()

    finally:
        service.close()

if __name__ == "__main__":
    asyncio.run(main())
