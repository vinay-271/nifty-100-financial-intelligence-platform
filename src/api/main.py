import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routers import (
    company,
    documents,
    health,
    peers,
    portfolio,
    screener,
    sectors,
    valuation,
)


logging.basicConfig(
    level=logging.INFO,
    format=(
        "%(asctime)s | "
        "%(levelname)s | "
        "%(name)s | "
        "%(message)s"
    ),
)

logger = logging.getLogger(
    "n100.api"
)


app = FastAPI(
    title="N100 Financial Intelligence API",
    description=(
        "REST API for the N100 Financial "
        "Intelligence Platform."
    ),
    version="1.0.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(
    health.router
)

app.include_router(
    company.router
)

app.include_router(
    screener.router
)

app.include_router(
    sectors.router
)

app.include_router(
    peers.router
)

app.include_router(
    valuation.router
)

app.include_router(
    portfolio.router
)

app.include_router(
    documents.router
)


@app.on_event("startup")
async def startup_event():
    logger.info(
        "N100 Financial Intelligence API started"
    )
