"""H-MAP ML microservice.

FastAPI app exposing endpoints used by the Laravel layer:

    POST /predict/forecast       Prophet weekly case forecast (city-wide or per-barangay)
    POST /predict/risk           Random Forest barangay risk classification
    POST /geocode                Street-address → (lat, lng) via Nominatim cascade

Models are loaded once at startup from ml/models/*.pkl (produced by
ml/train_prophet.py). The service runs bound to 127.0.0.1:5000 in production
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
from typing import Literal

import mysql.connector
import numpy as np
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
MODELS: dict[tuple[str, int | None], dict] = {}
# RandomForest: key is disease_code → bundle dict
RF_MODELS: dict[str, dict] = {}


def load_models() -> None:
    """Load every prophet_*.pkl and rf_*.pkl from MODEL_DIR into the in-memory registries."""
    MODELS.clear()
    RF_MODELS.clear()
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
        log.info("prophet loaded %s%s (mape=%s)",
                 code,
                 f"/bgy{bid}" if bid else " (city-wide)",
                 f"{bundle.get('validation_mape'):.1f}%" if bundle.get('validation_mape') is not None else "n/a")

    for path in sorted(MODEL_DIR.glob("rf_*.pkl")):
        try:
            with open(path, "rb") as f:
                bundle = pickle.load(f)
        except Exception as e:
            log.error("failed to load %s: %s", path.name, e)
            continue
        code = bundle.get("disease_code")
        if not code:
            log.warning("skipping %s — missing disease_code in bundle", path.name)
            continue
        RF_MODELS[code] = bundle
        log.info("rf loaded %s (accuracy=%s)",
                 code,
                 f"{bundle.get('accuracy'):.3f}" if bundle.get('accuracy') is not None else "n/a")

    log.info("model registry: %d prophet + %d rf models loaded", len(MODELS), len(RF_MODELS))


def _resolve_model(disease_code: str, barangay_id: int | None) -> tuple[dict, str]:
    """Pick the best available model for the requested (disease, barangay).

    Falls back from per-barangay → city-wide if no per-barangay model exists.
    Returns (bundle, resolution) where resolution is 'per_barangay' or 'city_wide_fallback'.
    """
    if barangay_id is not None:
        bundle = MODELS.get((disease_code, barangay_id))
        if bundle is not None:
            return bundle, "per_barangay"
    bundle = MODELS.get((disease_code, None))
    if bundle is not None:
        return bundle, ("city_wide_fallback" if barangay_id is not None else "city_wide")
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"No Prophet model available for disease_code={disease_code!r}"
               + (f" or city-wide fallback" if barangay_id else ""),
    )


# ─── Lifecycle ───────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("hmap-ml starting up (MODEL_DIR=%s)", MODEL_DIR)
    load_models()
    yield
    log.info("hmap-ml shutting down")


app = FastAPI(
    title="H-MAP ML Service",
    description="Disease forecasting and barangay risk classification for H-MAP.",
    version="0.2.0",
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
    }


@app.get("/models", tags=["ops"])
def list_models() -> list[dict]:
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
        })
    return out


# ─── /predict/forecast ──────────────────────────────────────────────────────

class ForecastRequest(BaseModel):
    disease_code: str = Field(..., description="PIDSR disease code, e.g. 'DENGUE'")
    barangay_id: int | None = Field(
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
    barangay_id: int | None
    barangay_name: str | None
    model: Literal["prophet"] = "prophet"
    resolution: Literal["per_barangay", "city_wide", "city_wide_fallback"]
    validation_mape: float | None
    training_tail_week: date
    forecast_anchor_week: date
    weeks_bridged: int = Field(
        ..., description="Weeks between training-tail and forecast-anchor. >0 means "
                         "the forecast extrapolates past the end of training data; "
                         "panel/dashboard should treat large values as lower confidence."
    )
    points: list[ForecastPoint]


def _this_week_monday() -> "pd.Timestamp":
    """The ISO-week Monday of the current calendar date (server clock)."""
    import pandas as pd
    today = pd.Timestamp.today().normalize()
    return today - pd.Timedelta(days=today.weekday())


@app.post("/predict/forecast", response_model=ForecastResponse, tags=["predict"])
def predict_forecast(req: ForecastRequest) -> ForecastResponse:
    log.info("forecast disease=%s barangay=%s weeks=%d",
             req.disease_code, req.barangay_id, req.weeks_ahead)

    bundle, resolution = _resolve_model(req.disease_code, req.barangay_id)
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
        total_periods = req.weeks_ahead
    else:
        bridge_weeks = int((anchor - training_tail).days // 7)
        weeks_bridged = max(0, bridge_weeks - 1)  # weeks strictly between tail and anchor
        total_periods = weeks_bridged + req.weeks_ahead

    future = model.make_future_dataframe(periods=total_periods, freq="W-MON",
                                          include_history=False)
    forecast = model.predict(future)
    # Return only the tail slice the caller asked for
    forecast_slice = forecast.tail(req.weeks_ahead)

    points = [
        ForecastPoint(
            week_start=row["ds"].date(),
            predicted_cases=max(0.0, float(row["yhat"])),
            lower_bound=max(0.0, float(row["yhat_lower"])),
            upper_bound=max(0.0, float(row["yhat_upper"])),
        )
        for _, row in forecast_slice.iterrows()
    ]

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


# ─── /predict/risk ──────────────────────────────────────────────────────────

class RiskRequest(BaseModel):
    disease_code: str
    morbidity_year: int = Field(..., ge=2010, le=2100,
                                 description="Year to classify, e.g. 2026")
    morbidity_week: int = Field(..., ge=1, le=53,
                                 description="ISO morbidity week (1-53)")


class RiskScore(BaseModel):
    barangay_id: int
    barangay_name: str
    risk_class: Literal["Low", "Moderate", "High"]
    probabilities: dict[str, float]
    current_cases: int
    mean_5yr: float
    threshold: float


class RiskResponse(BaseModel):
    disease_code: str
    morbidity_year: int
    morbidity_week: int
    model: Literal["random_forest"] = "random_forest"
    accuracy: float | None
    scores: list[RiskScore]


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


def _build_risk_features(conn, disease_code: str, year: int, week: int) -> list[dict]:
    """For each of the 16 barangays, build the 8-feature vector needed by the RF.

    Mirrors the feature engineering in ml/train_rf.py:build_features_and_labels,
    but for a single (year, week) point against the full historical data in MySQL.
    """
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT disease_id FROM diseases WHERE disease_code = %s", (disease_code,))
    row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail=f"unknown disease_code={disease_code!r}")
    disease_id = row["disease_id"]

    # Pull all weekly counts for this disease across the 11-year window we need
    # (current year, prior year, plus 5-year baseline).
    cur.execute(
        """SELECT barangay_id, morbidity_year, morbidity_week, COUNT(*) AS cases
             FROM cases
            WHERE disease_id = %s
              AND case_classification IN ('Confirmed','Probable')
              AND morbidity_year BETWEEN %s AND %s
              AND status_flag = 'Active'
            GROUP BY barangay_id, morbidity_year, morbidity_week""",
        (disease_id, year - 5, year),
    )
    counts_by_key: dict[tuple[int, int, int], int] = {
        (r["barangay_id"], r["morbidity_year"], r["morbidity_week"]): int(r["cases"])
        for r in cur.fetchall()
    }

    cur.execute("SELECT barangay_id, barangay_name FROM barangays ORDER BY barangay_id")
    barangays = cur.fetchall()
    cur.close()

    rows: list[dict] = []
    baseline_years = list(range(year - 5, year))
    # Calendar month: real month of the ISO week's Monday. Must match the
    # feature engineering in train_rf.py — otherwise train/serve skew.
    import pandas as _pd
    try:
        month = _pd.Timestamp.fromisocalendar(year, min(week, 53), 1).month
    except ValueError:
        month = _pd.Timestamp.fromisocalendar(year, 52, 1).month
    for b in barangays:
        bid, bname = b["barangay_id"], b["barangay_name"]
        current = counts_by_key.get((bid, year, week), 0)
        prior_yr = counts_by_key.get((bid, year - 1, week), 0)
        baseline = [counts_by_key.get((bid, by, week), 0) for by in baseline_years]
        mean_5yr = float(np.mean(baseline))
        std_5yr = float(np.std(baseline, ddof=1)) if len(baseline) > 1 else 0.0
        threshold = mean_5yr + 2 * std_5yr
        ratio = current / mean_5yr if mean_5yr > 0 else (1.0 if current == 0 else 100.0)
        ratio = min(ratio, 100.0)
        ytd = sum(counts_by_key.get((bid, year, w), 0) for w in range(1, week + 1))
        rows.append({
            "barangay_id": bid,
            "barangay_name": bname,
            "current_cases": current,
            "prior_year_cases": prior_yr,
            "mean_5yr": mean_5yr,
            "threshold": threshold,
            "ratio_to_mean": ratio,
            "ytd_cases": ytd,
            "morbidity_week": week,
            "calendar_month": month,
        })
    return rows


@app.post("/predict/risk", response_model=RiskResponse, tags=["predict"])
def predict_risk(req: RiskRequest) -> RiskResponse:
    log.info("risk disease=%s year=%d week=%d",
             req.disease_code, req.morbidity_year, req.morbidity_week)

    bundle = RF_MODELS.get(req.disease_code)
    if bundle is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No Random Forest model for disease_code={req.disease_code!r}",
        )
    clf = bundle["model"]
    feature_cols = bundle["feature_cols"]
    classes = list(clf.classes_)

    conn = _db_connect()
    try:
        feature_rows = _build_risk_features(conn, req.disease_code, req.morbidity_year, req.morbidity_week)
    finally:
        conn.close()

    X = np.array([[r[c] for c in feature_cols] for r in feature_rows], dtype=float)
    preds = clf.predict(X)
    probs = clf.predict_proba(X)

    scores: list[RiskScore] = []
    for r, pred, p in zip(feature_rows, preds, probs):
        scores.append(RiskScore(
            barangay_id=r["barangay_id"],
            barangay_name=r["barangay_name"],
            risk_class=pred,
            probabilities={cls: float(p[i]) for i, cls in enumerate(classes)},
            current_cases=int(r["current_cases"]),
            mean_5yr=round(r["mean_5yr"], 2),
            threshold=round(r["threshold"], 2),
        ))

    return RiskResponse(
        disease_code=req.disease_code,
        morbidity_year=req.morbidity_year,
        morbidity_week=req.morbidity_week,
        accuracy=bundle.get("accuracy"),
        scores=scores,
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
    lat: float | None
    lng: float | None
    geocode_source: Literal[
        "nominatim_street", "nominatim_subd", "nominatim_bgy_centroid",
        "manual_pin", "failed",
    ]
    geocode_query: str | None
    formatted: str | None
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
