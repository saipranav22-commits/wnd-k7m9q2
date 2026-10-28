import os
import shutil
import logging
from pathlib import Path

logger = logging.getLogger("aeris.config")

# Project Root resolution
PROJECT_ROOT = Path(__file__).resolve().parent.parent
BASE_DIR = PROJECT_ROOT

def resolve_sqlite_path() -> Path:
    """
    Locates the pre-populated SQLite database containing 1,584 actuals and 19,272 forecasts.
    In serverless environments (Vercel/Lambda), the code directory is strictly read-only.
    To avoid SQLite lock and read-only filesystem errors, the database is copied to /tmp/aeris.db.
    """
    is_serverless = bool(os.environ.get("VERCEL") or os.environ.get("AWS_LAMBDA_FUNCTION_NAME"))

    candidates = [
        Path("/tmp/aeris.db"),
        Path(os.environ.get("DATA_DIR", "")) / "aeris.db" if os.environ.get("DATA_DIR") else None,
        Path("E:/REintWindAnalytics/data/aeris.db"),
        PROJECT_ROOT / "data" / "aeris.db",
        PROJECT_ROOT / "api" / "aeris.db",
        PROJECT_ROOT / "backend" / "aeris.db",
        Path("data/aeris.db").resolve(),
        Path("api/aeris.db").resolve(),
        Path("backend/aeris.db").resolve(),
        Path("/var/task/data/aeris.db"),
        Path("/var/task/api/aeris.db"),
        Path("/var/task/backend/aeris.db"),
    ]

    source_db = None
    for cand in candidates:
        if cand and cand.exists() and cand.is_file() and cand.stat().st_size > 1_000_000:
            source_db = cand
            break

    # If in serverless runtime, copy to /tmp/aeris.db for full read-write & locking support
    if is_serverless:
        tmp_target = Path("/tmp/aeris.db")
        if tmp_target.exists() and tmp_target.stat().st_size > 6_000_000:
            return tmp_target

        if source_db and source_db != tmp_target:
            try:
                shutil.copyfile(source_db, tmp_target)
                return tmp_target
            except Exception as e:
                logger.warning(f"Could not copy database to /tmp: {e}")
                return source_db

        if source_db:
            return source_db

    # Standard local environment
    if source_db:
        return source_db

    return PROJECT_ROOT / "data" / "aeris.db"

IS_VERCEL = bool(os.environ.get("VERCEL"))
DATABASE_PATH = resolve_sqlite_path()
DATA_DIR = DATABASE_PATH.parent

if not IS_VERCEL and not DATABASE_PATH.exists():
    DATA_DIR.mkdir(parents=True, exist_ok=True)

# Format DATABASE_URL
if str(DATABASE_PATH).startswith("/tmp") or os.access(DATABASE_PATH.parent, os.W_OK):
    DATABASE_URL = os.environ.get("DATABASE_URL", f"sqlite:///{DATABASE_PATH.as_posix()}")
else:
    # Read-only URI fallback if filesystem is strictly read-only
    DATABASE_URL = os.environ.get("DATABASE_URL", f"sqlite:///{DATABASE_PATH.as_posix()}?mode=ro&uri=true")

# Elexon API Endpoints
ELEXON_BASE_URL = "https://data.elexon.co.uk/bmrs/api/v1"
ELEXON_FUELHH_URL = f"{ELEXON_BASE_URL}/datasets/FUELHH/stream"
ELEXON_WINDFOR_URL = f"{ELEXON_BASE_URL}/datasets/WINDFOR/stream"

# Decision defaults
DEFAULT_DECISION_CUTOFF_TIME = "11:00"  # Typical Day-Ahead auction submission window
TIMEZONE_UK = "Europe/London"

# Analysis default period
DEFAULT_DECISION_START_DATE = "2026-01-01"
DEFAULT_DECISION_END_DATE = "2026-01-31"
DEFAULT_DELIVERY_START_DATE = "2026-01-02"
DEFAULT_DELIVERY_END_DATE = "2026-02-01"

# Ingestion settings
REQUEST_TIMEOUT_SECONDS = 30.0
MAX_RETRIES = 3
INITIAL_BACKOFF_SECONDS = 1.0
