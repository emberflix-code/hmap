"""H-MAP Prophet training: weekly case forecasting per disease (+ per-barangay).

Reads `hmap_db.cases` and trains:
  • One Prophet model per disease where `diseases.forecast_enabled = 1`
    (city-wide weekly counts).
  • One Prophet model per (disease, barangay) pair where the pair has
    ≥ BARANGAY_VOLUME_FLOOR (default 200) Confirmed+Probable cases over
    the training window. Lower-volume pairs fall back to the city-wide
    model at serving time, scaled by barangay population share.

Methodology follows Olana et al. (2025) and Chakraborty et al. (2019):
  - Weekly aggregation (week start = ISO Monday)
  - Train on Confirmed+Probable only (matches threshold computation)
  - Yearly seasonality enabled; weekly/daily disabled (we have weekly grain)
  - Multiplicative seasonality (case counts scale with the trend baseline,
    which matches dengue's outbreak-year amplification)
  - Default Prophet uncertainty band (80% by default; we expose 95% too)

Temporal hold-out validation per the thesis (Ch.3 "Model Validation"):
  Train on years [start..HOLDOUT_START-1], validate on years
  [HOLDOUT_START..HOLDOUT_END]. Report MAPE on the held-out weeks.
  Default holdout = 2024-2025, training = 2010-2023.

After validation, a final model is refit on the full training window
[start..HOLDOUT_END] and serialized to ml/models/*.pkl for the FastAPI
service. The pickle filename embeds the disease_code and (optionally)
barangay_id so the service can load by lookup.

Usage:
    python ml/train_prophet.py                       # all 6 forecast-enabled diseases
    python ml/train_prophet.py --disease DENGUE      # one disease only
    python ml/train_prophet.py --no-barangay         # skip per-barangay tier
    python ml/train_prophet.py --holdout-start 2024 --holdout-end 2025
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import pickle
import sys
import warnings
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import mysql.connector
from dotenv import load_dotenv


def _ensure_tbb_on_path() -> None:
    """Prophet's prophet_model.bin needs tbb.dll on Windows. Cmdstan provides it
    but doesn't auto-add to PATH. Prepend the tbb directory if it exists."""
    if sys.platform != "win32":
        return
    candidates = [
        Path.home() / ".cmdstan" / "cmdstan-2.39.0" / "stan" / "lib" / "stan_math" / "lib" / "tbb",
    ]
    # Also look under prophet's bundled cmdstan if it actually has TBB
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


def _ensure_working_cmdstan() -> None:
    """Prophet's CmdStanPyBackend unconditionally points cmdstanpy at its
    bundled cmdstan dir if that directory exists — even when the bundled dir
    is gutted (missing makefile, as ships in some prophet wheels). That makes
    `Prophet()` raise AttributeError on `stan_backend` because every backend
    fails silently and falls through.

    Workaround: if prophet's bundled cmdstan dir exists but is invalid, AND
    we have a working full cmdstan at ~/.cmdstan, monkey-patch cmdstanpy.
    set_cmdstan_path to a no-op so prophet's set call doesn't poison it,
    then pin cmdstanpy to the working install.
    """
    try:
        import prophet as _p
    except Exception:
        return
    prophet_dir = Path(_p.__file__).parent / "stan_model"
    bundled = list(prophet_dir.glob("cmdstan-*"))
    if not bundled:
        return
    # A valid cmdstan has a makefile at its root
    if any((b / "makefile").exists() for b in bundled):
        return  # bundled is fine; nothing to do

    working = Path.home() / ".cmdstan" / "cmdstan-2.39.0"
    if not (working / "makefile").exists():
        log.warning("Prophet bundled cmdstan is gutted and no working cmdstan "
                    "found at %s. Prophet will fail.", working)
        return

    import cmdstanpy
    cmdstanpy.set_cmdstan_path(str(working))
    # Neutralize prophet's later set_cmdstan_path call
    cmdstanpy.set_cmdstan_path = lambda p: None
    log.info("Routed prophet around gutted bundled cmdstan → %s", working)


_ensure_tbb_on_path()

# Prophet is chatty — silence cmdstanpy progress bars and stan output
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning)
logging.getLogger("cmdstanpy").setLevel(logging.WARNING)
logging.getLogger("prophet").setLevel(logging.WARNING)

logging.basicConfig(
    level=os.getenv("ML_LOG_LEVEL", "info").upper(),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
log = logging.getLogger("hmap.prophet")

_ensure_working_cmdstan()

from prophet import Prophet  # noqa: E402

HERE = Path(__file__).resolve().parent
MODEL_DIR = HERE / "models"
REPORTS_DIR = HERE / "reports"

BARANGAY_VOLUME_FLOOR = 200  # min Confirmed+Probable cases for a (disease, barangay) model


# ─── DB ──────────────────────────────────────────────────────────────────────

def connect():
    load_dotenv(HERE / ".env")
    return mysql.connector.connect(
        host=os.environ["DB_HOST"],
        port=int(os.getenv("DB_PORT", "3306")),
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        database=os.getenv("DB_NAME", "hmap_db"),
        charset="utf8mb4",
    )


def forecast_enabled_diseases(conn) -> list[tuple[int, str, str]]:
    cur = conn.cursor()
    cur.execute(
        """SELECT disease_id, disease_code, disease_name
             FROM diseases
            WHERE forecast_enabled = 1
            ORDER BY display_order"""
    )
    return cur.fetchall()


def weekly_series(conn, disease_id: int, barangay_id: int | None,
                  year_start: int, year_end: int) -> pd.DataFrame:
    """Confirmed+Probable weekly case counts as a Prophet-ready dataframe.

    Returns columns ds (week-start date) and y (case count). Weeks with zero
    cases are filled in so Prophet sees a continuous time index — this matters
    for seasonality detection.
    """
    cur = conn.cursor()
    if barangay_id is None:
        cur.execute(
            """SELECT morbidity_year, morbidity_week, COUNT(*)
                 FROM cases
                WHERE disease_id = %s
                  AND case_classification IN ('Confirmed','Probable')
                  AND morbidity_year BETWEEN %s AND %s
                  AND status_flag = 'Active'
                GROUP BY morbidity_year, morbidity_week
                ORDER BY morbidity_year, morbidity_week""",
            (disease_id, year_start, year_end),
        )
    else:
        cur.execute(
            """SELECT morbidity_year, morbidity_week, COUNT(*)
                 FROM cases
                WHERE disease_id = %s
                  AND barangay_id = %s
                  AND case_classification IN ('Confirmed','Probable')
                  AND morbidity_year BETWEEN %s AND %s
                  AND status_flag = 'Active'
                GROUP BY morbidity_year, morbidity_week
                ORDER BY morbidity_year, morbidity_week""",
            (disease_id, barangay_id, year_start, year_end),
        )
    rows = cur.fetchall()
    if not rows:
        return pd.DataFrame(columns=["ds", "y"])

    df = pd.DataFrame(rows, columns=["year", "week", "y"])
    # Convert ISO year+week → week-start Monday date
    df["ds"] = df.apply(lambda r: _isoweek_monday(int(r["year"]), int(r["week"])), axis=1)
    df = df[["ds", "y"]].sort_values("ds").reset_index(drop=True)

    # Fill missing weeks with 0 so Prophet sees a continuous series
    if len(df) > 0:
        full_range = pd.date_range(df["ds"].min(), df["ds"].max(), freq="W-MON")
        df = df.set_index("ds").reindex(full_range, fill_value=0).rename_axis("ds").reset_index()
        df.columns = ["ds", "y"]
    return df


def _isoweek_monday(year: int, week: int) -> pd.Timestamp:
    """ISO 8601 year+week → Monday of that week as a pd.Timestamp."""
    # Cap week at 53; if a year doesn't have a week 53, fromisocalendar will raise.
    try:
        return pd.Timestamp.fromisocalendar(year, min(week, 53), 1)
    except ValueError:
        return pd.Timestamp.fromisocalendar(year, 52, 1)


def qualifying_barangays(conn, disease_id: int, year_start: int, year_end: int,
                          floor: int) -> list[tuple[int, str]]:
    cur = conn.cursor()
    cur.execute(
        """SELECT b.barangay_id, b.barangay_name, COUNT(*) AS n
             FROM cases c
             JOIN barangays b ON b.barangay_id = c.barangay_id
            WHERE c.disease_id = %s
              AND c.case_classification IN ('Confirmed','Probable')
              AND c.morbidity_year BETWEEN %s AND %s
              AND c.status_flag = 'Active'
            GROUP BY b.barangay_id, b.barangay_name
           HAVING n >= %s
            ORDER BY n DESC""",
        (disease_id, year_start, year_end, floor),
    )
    return [(bid, name) for bid, name, _ in cur.fetchall()]


# ─── Prophet ─────────────────────────────────────────────────────────────────

def fit_prophet(train_df: pd.DataFrame) -> Prophet:
    """Fit a Prophet model with H-MAP defaults."""
    # If all values are zero, Prophet warns and produces a flat zero forecast.
    # That's fine — we let it through so downstream code uniformly handles every series.
    m = Prophet(
        yearly_seasonality=True,
        weekly_seasonality=False,
        daily_seasonality=False,
        seasonality_mode="multiplicative",
        interval_width=0.80,  # 80% confidence band per WHO/CESU convention
    )
    m.fit(train_df)
    return m


def mape(actual: np.ndarray, predicted: np.ndarray) -> float:
    """Mean Absolute Percentage Error, robust to zero weeks.

    Standard MAPE blows up on zero-actual weeks. We use a smoothed denominator
    (actual + 1) to keep the metric finite. This is the same trick Olana et al.
    used; not to be confused with sMAPE.
    """
    actual = np.asarray(actual, dtype=float)
    predicted = np.asarray(predicted, dtype=float)
    return float(np.mean(np.abs((actual - predicted) / (actual + 1)) * 100))


def rmse(actual: np.ndarray, predicted: np.ndarray) -> float:
    actual = np.asarray(actual, dtype=float)
    predicted = np.asarray(predicted, dtype=float)
    return float(np.sqrt(np.mean((actual - predicted) ** 2)))


def naive_seasonal_forecast(full_series: pd.DataFrame, test_df: pd.DataFrame) -> np.ndarray:
    """Last-year-same-week baseline (a.k.a. seasonal-naive y_hat_t = y_{t-52}).

    Standard epi-surveillance baseline. If Prophet can't beat this, the model
    isn't earning its complexity. For weeks with no prior-year value (very
    early series), fall back to the train-window mean.
    """
    indexed = full_series.set_index("ds")["y"]
    train_mean = float(full_series.loc[~full_series["ds"].isin(test_df["ds"]), "y"].mean())
    out = []
    for ds in test_df["ds"]:
        prior = ds - pd.Timedelta(weeks=52)
        if prior in indexed.index:
            out.append(float(indexed.loc[prior]))
        else:
            out.append(train_mean)
    return np.asarray(out, dtype=float)


@dataclass
class TrainResult:
    disease_code: str
    barangay_id: int | None
    barangay_name: str | None
    n_weeks_total: int
    n_weeks_train: int
    n_weeks_holdout: int
    mape_holdout: float | None
    rmse_holdout: float | None
    mape_baseline: float | None
    rmse_baseline: float | None
    model_path: Path


def train_one(disease_id: int, disease_code: str,
              barangay_id: int | None, barangay_name: str | None,
              conn, args) -> TrainResult | None:
    """Train one Prophet model with temporal hold-out validation.

    Returns None if there aren't enough weeks to validate.
    """
    series = weekly_series(conn, disease_id, barangay_id, args.year_start, args.holdout_end)
    if series.empty or len(series) < 26:
        log.warning("skip %s%s — only %d weeks of data",
                    disease_code,
                    f"/barangay={barangay_id}" if barangay_id else "",
                    len(series))
        return None

    # Hold-out split
    holdout_mask = series["ds"].dt.year >= args.holdout_start
    train_df = series.loc[~holdout_mask].copy()
    test_df = series.loc[holdout_mask].copy()

    if len(train_df) < 26:
        log.warning("skip %s%s — only %d training weeks",
                    disease_code, f"/barangay={barangay_id}" if barangay_id else "",
                    len(train_df))
        return None

    # Validation (skip if too sparse to produce a meaningful holdout)
    mape_holdout = None
    rmse_holdout = None
    mape_baseline = None
    rmse_baseline = None
    if len(test_df) > 0:
        m_val = fit_prophet(train_df)
        future = m_val.make_future_dataframe(periods=len(test_df), freq="W-MON",
                                              include_history=False)
        if len(future) > 0:
            fc = m_val.predict(future)
            if len(fc) >= len(test_df):
                actual = test_df["y"].values
                predicted = fc["yhat"].values[:len(actual)]
                mape_holdout = mape(actual, predicted)
                rmse_holdout = rmse(actual, predicted)

                # Seasonal-naive baseline on the same hold-out weeks
                baseline = naive_seasonal_forecast(series, test_df)
                mape_baseline = mape(actual, baseline)
                rmse_baseline = rmse(actual, baseline)

    # Refit on the full window for serving
    m_serve = fit_prophet(series)

    # Save
    MODEL_DIR.mkdir(exist_ok=True)
    if barangay_id is None:
        path = MODEL_DIR / f"prophet_{disease_code}.pkl"
    else:
        path = MODEL_DIR / f"prophet_{disease_code}_bgy{barangay_id}.pkl"
    with open(path, "wb") as f:
        pickle.dump(
            {
                "model": m_serve,
                "disease_code": disease_code,
                "barangay_id": barangay_id,
                "barangay_name": barangay_name,
                "trained_weeks": len(series),
                "training_window": (args.year_start, args.holdout_end),
                "validation_holdout": (args.holdout_start, args.holdout_end),
                "validation_mape": mape_holdout,
                "validation_rmse": rmse_holdout,
                "baseline_strategy": "seasonal_naive_lag52",
                "baseline_mape": mape_baseline,
                "baseline_rmse": rmse_baseline,
            },
            f,
        )

    return TrainResult(
        disease_code=disease_code,
        barangay_id=barangay_id,
        barangay_name=barangay_name,
        n_weeks_total=len(series),
        n_weeks_train=len(train_df),
        n_weeks_holdout=len(test_df),
        mape_holdout=mape_holdout,
        rmse_holdout=rmse_holdout,
        mape_baseline=mape_baseline,
        rmse_baseline=rmse_baseline,
        model_path=path,
    )


# ─── Reporting ───────────────────────────────────────────────────────────────

def report(results: list[TrainResult]) -> None:
    bar = "=" * 92
    print()
    print(bar)
    print("  Prophet training results  (baseline = seasonal-naive, lag 52 weeks)")
    print(bar)
    print(f"  {'Disease':<8} {'Barangay':<24} {'Weeks':>6} {'Train':>6} {'Hold':>5} "
          f"{'MAPE%':>7} {'baseMAPE%':>9} {'lift':>6}")
    print(f"  {'-'*8:<8} {'-'*24:<24} {'-'*6:>6} {'-'*6:>6} {'-'*5:>5} "
          f"{'-'*7:>7} {'-'*9:>9} {'-'*6:>6}")
    for r in results:
        bgy = r.barangay_name or "(city-wide)"
        bgy = bgy.encode("ascii", "replace").decode("ascii")
        mape_str = f"{r.mape_holdout:.1f}" if r.mape_holdout is not None else "n/a"
        base_str = f"{r.mape_baseline:.1f}" if r.mape_baseline is not None else "n/a"
        if r.mape_holdout is not None and r.mape_baseline is not None:
            lift = r.mape_baseline - r.mape_holdout  # +ve means Prophet wins
            lift_str = f"{lift:+.1f}"
        else:
            lift_str = "n/a"
        print(f"  {r.disease_code:<8} {bgy:<24} {r.n_weeks_total:>6} {r.n_weeks_train:>6} "
              f"{r.n_weeks_holdout:>5} {mape_str:>7} {base_str:>9} {lift_str:>6}")
    print(bar)
    print(f"  {len(results)} models written to {MODEL_DIR}")
    print(bar)


def write_reports(results: list[TrainResult], args) -> None:
    """Persist Prophet evaluation metrics to ml/reports/ for the thesis."""
    if not results:
        return
    REPORTS_DIR.mkdir(exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    summary = {
        "generated_at_utc": ts,
        "training_window": [args.year_start, args.holdout_end],
        "validation_holdout": [args.holdout_start, args.holdout_end],
        "baseline_strategy": "seasonal_naive_lag52",
        "models": [
            {
                "disease_code": r.disease_code,
                "barangay_id": r.barangay_id,
                "barangay_name": r.barangay_name,
                "n_weeks_total": r.n_weeks_total,
                "n_weeks_train": r.n_weeks_train,
                "n_weeks_holdout": r.n_weeks_holdout,
                "mape_prophet": r.mape_holdout,
                "rmse_prophet": r.rmse_holdout,
                "mape_baseline": r.mape_baseline,
                "rmse_baseline": r.rmse_baseline,
                "mape_lift_vs_baseline": (r.mape_baseline - r.mape_holdout)
                    if r.mape_holdout is not None and r.mape_baseline is not None else None,
            }
            for r in results
        ],
    }
    json_path = REPORTS_DIR / f"prophet_eval_{ts}.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    csv_path = REPORTS_DIR / f"prophet_eval_{ts}.csv"
    with open(csv_path, "w", encoding="utf-8") as f:
        f.write("disease,barangay_id,barangay_name,n_weeks_total,n_weeks_train,n_weeks_holdout,"
                "mape_prophet,rmse_prophet,mape_baseline,rmse_baseline,mape_lift\n")
        for r in results:
            name = (r.barangay_name or "city-wide").replace(",", " ")
            def _f(v): return f"{v:.4f}" if v is not None else ""
            lift = (r.mape_baseline - r.mape_holdout) if r.mape_holdout is not None and r.mape_baseline is not None else None
            f.write(f"{r.disease_code},{r.barangay_id or ''},{name},"
                    f"{r.n_weeks_total},{r.n_weeks_train},{r.n_weeks_holdout},"
                    f"{_f(r.mape_holdout)},{_f(r.rmse_holdout)},"
                    f"{_f(r.mape_baseline)},{_f(r.rmse_baseline)},{_f(lift)}\n")

    latest_json = REPORTS_DIR / "prophet_eval_latest.json"
    latest_csv = REPORTS_DIR / "prophet_eval_latest.csv"
    latest_json.write_text(json_path.read_text(encoding="utf-8"), encoding="utf-8")
    latest_csv.write_text(csv_path.read_text(encoding="utf-8"), encoding="utf-8")
    print(f"  Eval report: {json_path.name}, {csv_path.name}")


# ─── Entry ───────────────────────────────────────────────────────────────────

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--year-start", type=int, default=2010)
    p.add_argument("--holdout-start", type=int, default=2024,
                   help="First year held out for validation")
    p.add_argument("--holdout-end", type=int, default=2025,
                   help="Last year included in training+validation (2026 is YTD so excluded)")
    p.add_argument("--disease", default=None,
                   help="Train only this disease_code (e.g. DENGUE); default all forecast_enabled")
    p.add_argument("--no-barangay", action="store_true",
                   help="Skip the per-barangay tier")
    p.add_argument("--barangay-floor", type=int, default=BARANGAY_VOLUME_FLOOR,
                   help="Min Confirmed+Probable cases for a (disease, barangay) model")
    args = p.parse_args()

    conn = connect()
    results: list[TrainResult] = []
    try:
        diseases = forecast_enabled_diseases(conn)
        if args.disease:
            diseases = [d for d in diseases if d[1] == args.disease]
            if not diseases:
                print(f"ERROR: no forecast-enabled disease with code {args.disease!r}", file=sys.stderr)
                sys.exit(2)

        for disease_id, code, name in diseases:
            log.info("training city-wide %s (%s)", code, name)
            r = train_one(disease_id, code, None, None, conn, args)
            if r:
                results.append(r)

            if args.no_barangay:
                continue
            barangays = qualifying_barangays(conn, disease_id, args.year_start, args.holdout_end, args.barangay_floor)
            for bid, bname in barangays:
                log.info("training %s/%s", code, bname)
                r = train_one(disease_id, code, bid, bname, conn, args)
                if r:
                    results.append(r)
    finally:
        conn.close()

    report(results)
    write_reports(results, args)


if __name__ == "__main__":
    main()
