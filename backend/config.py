import os
from pathlib import Path

# Dynamic Path Resolution: checks environment variable, local E: drive (if present and not Vercel), or project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if os.environ.get("VERCEL"):
    BASE_DIR = PROJECT_ROOT
elif os.path.exists("E:/REintWindAnalytics/data/aeris.db"):
    BASE_DIR = Path("E:/REintWindAnalytics")
else:
    BASE_DIR = PROJECT_ROOT

DATA_DIR = Path(os.environ.get("DATA_DIR", BASE_DIR / "data"))
if not os.environ.get("VERCEL"):
    DATA_DIR.mkdir(parents=True, exist_ok=True)

DATABASE_PATH = DATA_DIR / "aeris.db"
# If running in serverless / read-only deployment, allow URI query params
IS_VERCEL = bool(os.environ.get("VERCEL"))
DATABASE_URL = os.environ.get("DATABASE_URL", f"sqlite:///{DATABASE_PATH.as_posix()}")

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
