from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATA_DIR = PROJECT_ROOT / "data"

CORE_DATA = DATA_DIR / "raw" / "core"

SUPPORTING_DATA = DATA_DIR / "raw" / "supporting"

PROCESSED_DATA = DATA_DIR / "processed"

OUTPUT_DIR = DATA_DIR / "output"

LOG_DIR = PROJECT_ROOT / "logs"

DB_DIR = PROJECT_ROOT / "db"

DB_FILE = DB_DIR / "nifty100.db"
