"""H-MAP ML microservice.

FastAPI app exposing endpoints used by the Laravel layer:

    POST /predict/forecast       Prophet weekly case forecast (city-wide or per-barangay)
    POST /predict/trend          Rising / not-rising 4-week trend for all 16 barangays
    POST /geocode                Street-address → (lat, lng) via Nominatim cascade

Models are loaded once at startup from ml/models/*.pkl (produced by
ml/train_prophet.py). A model is served only if it beat the seasonal-naive
(same week last year) baseline on its hold-out data (Ch.3 Module 5), because
Prophet does not perform well on every disease. Barangay risk tiers are
rule-based and computed in Laravel (App\\Services\\RiskTiers); the Random Forest
classifier was retired with the revised Ch.3. The service runs bound to 127.0.0.1:5000 in production
(per docs/architecture.md) and is NOT exposed to the public internet — Laravel
proxies authenticated requests via Guzzle.
"""

from __future__ import annotations

import logging
import os
import pickle
import sys
from contextlib import asynccontextmanager
from datetime import date, timedelta
from pathlib import Path
from typing import Dict, List, Literal, Optional, Tuple

import mysql.connector
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field

from geocode import geocode_case_address

logging.basicConfig(
    level=os.getenv("ML_LOG_LEVEL", "info").upper(),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
log = logging.getLogger("hmap.ml")

HERE = Path(__file__).resolve().parent
MODEL_DIR = Path(os.getenv("MODEL_DIR", HERE / "models"))


def _ensure_tbb_on_path() -> None:
    """Prophet's prophet_model.bin needs tbb.dll on Windows. Same trick as
    train_prophet.py — must run before Prophet is imported indirectly via unpickle."""
    if sys.platform != "win32":
        return
    candidates = [
        Path.home() / ".cmdstan" / "cmdstan-2.39.0" / "stan" / "lib" / "stan_math" / "lib" / "tbb",
    ]
    try:
        import prophet as _p
        prophet_dir = Path(_p.__file__).parent / "stan_model"
        for sub in prophet_dir.glob("cmdstan-*/stan/lib/stan_math/lib/tbb"):
            candidates.append(sub)
    except Exception:
        pass
    for c in candidates:
        if (c / "tbb.dll").exists():
            os.environ["PATH"] = f"{c};{os.environ.get('PATH', '')}"
            return


_ensure_tbb_on_path()


# ─── Model registry ──────────────────────────────────────────────────────────

# Prophet: key is (disease_code, barangay_id or None) → model bundle dict
MODELS: Dict[Tuple[str, Optional[int]], dict] = {}


def outperforms_baseline(bundle: dict) -> bool:
    """True if the model's hold-out MAPE beat the seasonal-naive baseline.

    This is the display check in Ch.3 Module 5: an operational safeguard, not
    model development. Bundles without a baseline comparison are not served.
    """
    mape, base = bundle.get("validation_mape"), bundle.get("baseline_mape")
    return mape is not None and base is not None and mape < base


def load_models() -> None:
    """Load every prophet_*.pkl from MODEL_DIR into the in-memory registry."""
    MODELS.clear()
    if not MODEL_DIR.exists():
        log.warning("MODEL_DIR %s does not exist — no models available", MODEL_DIR)
        return

    for path in sorted(MODEL_DIR.glob("prophet_*.pkl")):
        try:
            with open(path, "rb") as f:
                bundle = pickle.load(f)
        except Exception as e:
            log.error("failed to load %s: %s", path.name, e)
            continue
        code = bundle.get("disease_code")
        bid = bundle.get("barangay_id")
        if not code:
            log.warning("skipping %s — missing disease_code in bundle", path.name)
            continue
        MODELS[(code, bid)] = bundle
        log.info("prophet loaded %s%s (mape=%s, baseline=%s, served=%s)",
                 code,
                 f"/bgy{bid}" if bid else " (city-wide)",
                 f"{bundle.get('validation_mape'):.1f}%" if bundle.get('validation_mape') is not None else "n/a",
                 f"{bundle.get('baseline_mape'):.1f}%" if bundle.get('baseline_mape') is not None else "n/a",
                 outperforms_baseline(bundle))

    served = sum(outperforms_baseline(b) for b in MODELS.values())
    log.info("model registry: %d prophet models loaded, %d outperform the baseline and are served",
             len(MODELS), served)


def _resolve_model(disease_code: str, barangay_id: Optional[int]) -> Tuple[dict, str]:
    """Pick the best servable model for the requested (disease, barangay).

    Falls back from per-barangay → city-wide when no per-barangay model exists
    or it did not beat the baseline. Returns (bundle, resolution).
    """
    if barangay_id is not None:
        bundle = MODELS.get((disease_code, barangay_id))
        if bundle is not None and outperforms_baseline(bundle):
            return bundle, "per_barangay"
    bundle = MODELS.get((disease_code, None))
    if bundle is not None and outperforms_baseline(bundle):
        return bundle, ("city_wide_fallback" if barangay_id is not None else "city_wide")
    if any(code == disease_code for code, _ in MODELS):
        detail = (f"Forecast not displayed for {disease_code!r}: the model did not outperform "
                  "the same-week-last-year comparison on its hold-out data.")
    else:
        detail = f"No Prophet model available for disease_code={disease_code!r}"
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


# ─── Lifecycle ───────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("hmap-ml starting up (MODEL_DIR=%s)", MODEL_DIR)
    load_models()
    yield
    log.info("hmap-ml shutting down")


app = FastAPI(
    title="H-MAP ML Service",
    description="Disease trend forecasting (existing Prophet model) and geocoding.",
    version="0.3.0",
    lifespan=lifespan,
)


# ─── /health ────────────────────────────────────────────────────────────────

@app.get("/health", tags=["ops"])
def health() -> dict:
    return {
        "status": "ok",
        "service": "hmap-ml",
        "models_loaded": len(MODELS),
        "diseases": sorted({code for code, _ in MODELS.keys()}),
        "forecast_diseases": sorted({code for (code, _), b in MODELS.items()
                                     if outperforms_baseline(b)}),
    }


@app.get("/models", tags=["ops"])
def list_models() -> List[dict]:
    """List every loaded model and its metadata. Useful for the admin panel."""
    out = []
    for (code, bid), bundle in sorted(MODELS.items(), key=lambda kv: (kv[0][0], kv[0][1] or 0)):
        out.append({
            "disease_code": code,
            "barangay_id": bid,
            "barangay_name": bundle.get("barangay_name"),
            "trained_weeks": bundle.get("trained_weeks"),
            "training_window": bundle.get("training_window"),
            "validation_holdout": bundle.get("validation_holdout"),
            "validation_mape": bundle.get("validation_mape"),
            "baseline_mape": bundle.get("baseline_mape"),
            "served": outperforms_baseline(bundle),
        })
    return out


# ─── /predict/forecast ──────────────────────────────────────────────────────

class ForecastRequest(BaseModel):
    disease_code: str = Field(..., description="PIDSR disease code, e.g. 'DENGUE'")
    barangay_id: Optional[int] = Field(
        None, ge=1, le=16,
        description="Parañaque barangay ID 1-16, or omit for city-wide forecast",
    )
    weeks_ahead: int = Field(4, ge=1, le=12, description="Forecast horizon in weeks")


class ForecastPoint(BaseModel):
    week_start: date
    predicted_cases: float
    lower_bound: float
    upper_bound: float


class ForecastResponse(BaseModel):
    disease_code: str
    barangay_id: Optional[int]
    barangay_name: Optional[str]
    model: Literal["prophet"] = "prophet"
    resolution: Literal["per_barangay", "city_wide", "city_wide_fallback"]
    validation_mape: Optional[float]
    training_tail_week: date
    forecast_anchor_week: date
    weeks_bridged: int = Field(
        ..., description="Weeks between training-tail and forecast-anchor. >0 means "
                         "the forecast extrapolates past the end of training data; "
                         "panel/dashboard should treat large values as lower confidence."
    )
    points: List[ForecastPoint]


def _this_week_monday() -> "pd.Timestamp":
    """The ISO-week Monday of the current calendar date (server clock)."""
    import pandas as pd
    today = pd.Timestamp.today().normalize()
    return today - pd.Timedelta(days=today.weekday())


FORECAST_SEED = 2026


def _forecast_points(bundle: dict, weeks_ahead: int) -> Tuple[List[ForecastPoint], "pd.Timestamp", "pd.Timestamp", int]:
    """Forecast `weeks_ahead` weeks from this week's Monday.

    Returns (points, training_tail, anchor, weeks_bridged).
    """
    model = bundle["model"]

    # Anchor the forecast at THIS week's Monday, not at the end of training
    # data. The 2026 PIDSR registry is deliberately YTD-excluded from training
    # (see train_prophet.py --holdout-end 2025), so there may be a multi-month
    # gap between training tail and "today". We extend the future dataframe to
    # bridge that gap and return only the requested weeks_ahead starting from
    # this-week's Monday. The dashboard renders an exact calendar horizon
    # without having to know about the training window.
    import pandas as pd
    training_tail = pd.Timestamp(model.history["ds"].max()).normalize()
    anchor = _this_week_monday()
    # Number of W-MON rows from training_tail+1week up to anchor-1week (the
    # bridge), plus the requested horizon starting at anchor.
    if anchor <= training_tail:
        # Edge case: model was retrained recently; anchor falls inside history.
        # Just forecast the next weeks_ahead from training_tail+1.
        weeks_bridged = 0
        total_periods = weeks_ahead
    else:
        bridge_weeks = int((anchor - training_tail).days // 7)
        weeks_bridged = max(0, bridge_weeks - 1)  # weeks strictly between tail and anchor
        total_periods = weeks_bridged + weeks_ahead

    future = model.make_future_dataframe(periods=total_periods, freq="W-MON",
                                          include_history=False)
    # Prophet draws its uncertainty interval by random simulation. A fixed seed
    # makes the same request return the same bounds every time, so the
    # dashboard figures do not change on refresh (Ch.4 test TC-FCT-02).
    import numpy as np
    np.random.seed(FORECAST_SEED)
    forecast = model.predict(future)
    # Return only the tail slice the caller asked for
    forecast_slice = forecast.tail(weeks_ahead)

    points = [
        ForecastPoint(
            week_start=row["ds"].date(),
            predicted_cases=max(0.0, float(row["yhat"])),
            lower_bound=max(0.0, float(row["yhat_lower"])),
            upper_bound=max(0.0, float(row["yhat_upper"])),
        )
        for _, row in forecast_slice.iterrows()
    ]
    return points, training_tail, anchor, weeks_bridged


@app.post("/predict/forecast", response_model=ForecastResponse, tags=["predict"])
def predict_forecast(req: ForecastRequest) -> ForecastResponse:
    log.info("forecast disease=%s barangay=%s weeks=%d",
             req.disease_code, req.barangay_id, req.weeks_ahead)

    bundle, resolution = _resolve_model(req.disease_code, req.barangay_id)
    points, training_tail, anchor, weeks_bridged = _forecast_points(bundle, req.weeks_ahead)

    return ForecastResponse(
        disease_code=req.disease_code,
        barangay_id=req.barangay_id,
        barangay_name=bundle.get("barangay_name"),
        resolution=resolution,
        validation_mape=bundle.get("validation_mape"),
        training_tail_week=training_tail.date(),
        forecast_anchor_week=anchor.date(),
        weeks_bridged=weeks_bridged,
        points=points,
    )


# ─── /predict/trend ─────────────────────────────────────────────────────────
# Input to the rule-based risk tier (Laravel App\Services\RiskTiers): whether
# each barangay's 4-week forecast is rising. Per-barangay models are used where
# they are served, otherwise the city-wide model applies to every barangay.

RISING_MIN_RATIO = 1.10   # last forecast week at least 10% above the first ...
RISING_MIN_CASES = 1.0    # ... and at least one case higher


class TrendRequest(BaseModel):
    disease_code: str
    weeks_ahead: int = Field(4, ge=2, le=12)


class BarangayTrend(BaseModel):
    barangay_id: int
    rising: bool
    first_week_cases: float
    last_week_cases: float
    resolution: Literal["per_barangay", "city_wide_fallback"]


class TrendResponse(BaseModel):
    disease_code: str
    forecast_anchor_week: date
    weeks_ahead: int
    trends: List[BarangayTrend]


def is_rising(first: float, last: float) -> bool:
    return last >= first * RISING_MIN_RATIO and (last - first) >= RISING_MIN_CASES


@app.post("/predict/trend", response_model=TrendResponse, tags=["predict"])
def predict_trend(req: TrendRequest) -> TrendResponse:
    log.info("trend disease=%s weeks=%d", req.disease_code, req.weeks_ahead)
    cache: Dict[int, Tuple[List[ForecastPoint], "pd.Timestamp"]] = {}
    trends: List[BarangayTrend] = []
    anchor = None
    for bid in range(1, 17):
        bundle, resolution = _resolve_model(req.disease_code, bid)
        key = id(bundle)  # the city-wide bundle is forecast once and reused
        if key not in cache:
            points, _tail, anchor, _bridged = _forecast_points(bundle, req.weeks_ahead)
            cache[key] = (points, anchor)
        points, anchor = cache[key]
        first, last = points[0].predicted_cases, points[-1].predicted_cases
        trends.append(BarangayTrend(barangay_id=bid, rising=is_rising(first, last),
                                    first_week_cases=round(first, 2),
                                    last_week_cases=round(last, 2), resolution=resolution))
    return TrendResponse(disease_code=req.disease_code, forecast_anchor_week=anchor.date(),
                         weeks_ahead=req.weeks_ahead, trends=trends)


def _db_connect():
    """Connect to hmap_db using the same env config the ETL/training scripts use."""
    load_dotenv(HERE / ".env")
    return mysql.connector.connect(
        host=os.environ["DB_HOST"],
        port=int(os.getenv("DB_PORT", "3306")),
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        database=os.getenv("DB_NAME", "hmap_db"),
        charset="utf8mb4",
    )


# ─── /geocode ───────────────────────────────────────────────────────────────
# Address → coordinates for case entry. Wraps ml/geocode.py's cache-backed
# cascade so the Laravel data-entry form can auto-locate addresses without
# duplicating the cascade logic in PHP. Cache hits return instantly; cache
# misses cost one Nominatim API call (~1.1s due to rate limiting).

class GeocodeRequest(BaseModel):
    street_purok: str = Field(..., min_length=1, max_length=255,
                              description="Raw StreetPurok-style address (e.g. 'QUIRINO AVE., 0549')")
    barangay: str = Field(..., min_length=1, max_length=80,
                          description="Canonical Parañaque barangay name")


class GeocodeResponse(BaseModel):
    success: bool
    lat: Optional[float]
    lng: Optional[float]
    geocode_source: Literal[
        "nominatim_street", "nominatim_subd", "nominatim_bgy_centroid",
        "manual_pin", "failed",
    ]
    geocode_query: Optional[str]
    formatted: Optional[str]
    from_cache: bool


@app.post("/geocode", response_model=GeocodeResponse, tags=["geocode"])
def geocode(req: GeocodeRequest) -> GeocodeResponse:
    """Geocode a single address via the cache + cascade pipeline.

    Returns the best in-Parañaque match. Frontend should treat
    geocode_source ∈ {nominatim_street, nominatim_subd, manual_pin} as
    'usable for clustering' and surface a confirmation pin to the encoder;
    geocode_source = nominatim_bgy_centroid as 'precision warning' so the
    encoder can drag the pin to a more accurate location (which would then
    be re-saved as manual_pin on case submission).
    """
    user_agent = os.getenv("NOMINATIM_USER_AGENT", "hmap-capstone").strip()
    conn = _db_connect()
    try:
        outcome, from_cache = geocode_case_address(
            conn, req.street_purok, req.barangay, user_agent
        )
        conn.commit()
    finally:
        conn.close()
    return GeocodeResponse(
        success=outcome.success,
        lat=outcome.lat,
        lng=outcome.lng,
        geocode_source=outcome.geocode_source,
        geocode_query=outcome.geocode_query,
        formatted=outcome.formatted,
        from_cache=from_cache,
    )
