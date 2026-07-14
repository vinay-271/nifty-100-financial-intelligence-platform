import os
from dotenv import load_dotenv

load_dotenv()

EXCEL_HEADER_ROW = int(
    os.getenv("EXCEL_HEADER_ROW", 1)
)

PROJECT_NAME = os.getenv("PROJECT_NAME")

DATABASE_PATH = os.getenv("DATABASE_PATH")

RAW_CORE = os.getenv("RAW_CORE")

RAW_SUPPORTING = os.getenv("RAW_SUPPORTING")

PROCESSED_DATA = os.getenv("PROCESSED_DATA")

OUTPUT_DIR = os.getenv("OUTPUT_DIR")

LOG_DIR = os.getenv("LOG_DIR")

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
