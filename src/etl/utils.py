from pathlib import Path
from loguru import logger

LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

logger.remove()

logger.add(
    LOG_DIR / "etl.log",
    rotation="5 MB",
    retention=5,
    level="INFO",
    enqueue=True,
)

logger.add(
    lambda msg: print(msg, end=""),
    level="INFO"
)
