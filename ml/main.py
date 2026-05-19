"""H-MAP ML microservice.

FastAPI app exposing two endpoints used by the Laravel layer:

    POST /predict/forecast       Prophet-based weekly case forecast for a (disease, barangay)
    POST /predict/risk           Random Forest barangay risk classification

This is the scaffolding skeleton. The actual model loading, feature engineering, and
inference logic come later. Right now both endpoints return stubbed responses so the
Laravel side can wire up its proxy and the frontend can mock against real HTTP shapes.
"""

from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from datetime import date
from typing import Literal

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field

logging.basicConfig(
    level=os.getenv("ML_LOG_LEVEL", "info").upper(),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
log = logging.getLogger("hmap.ml")


@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("hmap-ml starting up")
    # TODO: load models from disk into app.state
    yield
    log.info("hmap-ml shutting down")


app = FastAPI(
    title="H-MAP ML Service",
    description="Disease forecasting and barangay risk classification for H-MAP.",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/health", tags=["ops"])
def health() -> dict[str, str]:
    return {"status": "ok", "service": "hmap-ml"}


class ForecastRequest(BaseModel):
    disease_code: str = Field(..., description="PIDSR disease code, e.g. 'DENGUE'")
    barangay_id: int = Field(..., ge=1, le=16, description="Parañaque barangay ID 1-16")
    weeks_ahead: int = Field(4, ge=1, le=12, description="Forecast horizon in weeks")


class ForecastPoint(BaseModel):
    week_start: date
    predicted_cases: float
    lower_bound: float
    upper_bound: float


class ForecastResponse(BaseModel):
    disease_code: str
    barangay_id: int
    model: Literal["prophet"] = "prophet"
    points: list[ForecastPoint]


@app.post("/predict/forecast", response_model=ForecastResponse, tags=["predict"])
def predict_forecast(req: ForecastRequest) -> ForecastResponse:
    log.info("forecast disease=%s barangay=%d weeks=%d",
             req.disease_code, req.barangay_id, req.weeks_ahead)
    # TODO: load Prophet model, generate real forecast.
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Prophet forecasting not yet implemented; this is a scaffold.",
    )


class RiskRequest(BaseModel):
    disease_code: str
    week_start: date


class RiskScore(BaseModel):
    barangay_id: int
    risk_class: Literal["low", "moderate", "high", "critical"]
    score: float = Field(..., ge=0.0, le=1.0)


class RiskResponse(BaseModel):
    disease_code: str
    week_start: date
    model: Literal["random_forest"] = "random_forest"
    scores: list[RiskScore]


@app.post("/predict/risk", response_model=RiskResponse, tags=["predict"])
def predict_risk(req: RiskRequest) -> RiskResponse:
    log.info("risk disease=%s week=%s", req.disease_code, req.week_start)
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Random Forest risk classification not yet implemented; this is a scaffold.",
    )
