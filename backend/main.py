import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func

from backend.config import BASE_DIR, IS_VERCEL
from backend.models.database import init_db, SessionLocal, ActualWindGeneration, ForecastWindGeneration
from backend.services.ingestion import IngestionService
from backend.routers import health, metadata, overview, decisions, accuracy, records

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("aeris")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Only initialize DB schema and count records if not in serverless runtime
    if not IS_VERCEL:
        logger.info("Initializing database tables...")
        try:
            init_db()
            db = SessionLocal()
            try:
                act_cnt = db.query(func.count(ActualWindGeneration.id)).scalar() or 0
                fc_cnt = db.query(func.count(ForecastWindGeneration.id)).scalar() or 0
                logger.info(f"Existing records in SQLite: Actuals={act_cnt}, Forecasts={fc_cnt}")
            finally:
                db.close()
        except Exception as e:
            logger.warning(f"Database init check skipped: {e}")

    yield
    logger.info("AERIS backend shutting down.")

app = FastAPI(
    title="AERIS — Wind Forecast Intelligence",
    description="Day-Ahead Wind Generation & Forecast Accuracy Analytics Platform for UK Wholesale Power Market",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# Enable CORS for local Vite dev and Vercel production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount modular routers
app.include_router(health.router)
app.include_router(metadata.router)
app.include_router(overview.router)
app.include_router(decisions.router)
app.include_router(accuracy.router)
app.include_router(records.router)

# Mount frontend production build if available and not Vercel (where Vercel handles static routing directly)
from pathlib import Path
from fastapi.staticfiles import StaticFiles
if not IS_VERCEL:
    frontend_dist = BASE_DIR / "frontend" / "dist"
    if not frontend_dist.exists():
        frontend_dist = Path("frontend/dist")
    if frontend_dist.exists():
        app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="static")

@app.post("/api/admin/sync", tags=["Admin"])
async def trigger_sync(background_tasks: BackgroundTasks):
    """
    Trigger background synchronization with Elexon BMRS for January 2026 data.
    """
    async def run_sync():
        logger.info("Running background Elexon January 2026 data synchronization...")
        ingestion = IngestionService()
        try:
            results = await ingestion.run_full_january_sync()
            logger.info(f"Sync complete: {results}")
        except Exception as e:
            logger.error(f"Sync failed: {e}")
        finally:
            ingestion.close()

    background_tasks.add_task(run_sync)
    return {"status": "Sync initiated in background", "target_month": "January 2026"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
