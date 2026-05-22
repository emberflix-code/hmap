"""H-MAP Random Forest training: barangay risk classification per disease.

Per Ch.3 spec (p.40):
  - One RandomForestClassifier per forecast-enabled disease
  - 200 estimators, class_weight='balanced'
  - Labels: High if case count exceeds threshold for that week,
            Moderate if between historical mean and threshold,
            Low if at or below the mean
  - Features (8): barangay_id, morbidity_week, calendar_month,
                  current_week_cases, same_week_prior_year_cases,
                  five_year_historical_mean, ratio_current_to_mean,
                  cumulative_ytd_cases

LABEL LEAKAGE PREVENTION:
  The thesis text would let you compute labels using the current
  thresholds table (alert_year=2026, baseline 2021-2025). That leaks
  future data into historical labels. Instead, for each labeled
  (disease, barangay, year, week) row we compute the baseline mean+threshold
  using ONLY the prior 5 calendar years of cases for that (disease, week).
  This matches what an analyst would have known at the time.

TEMPORAL HOLD-OUT:
  Train 2010-2023, validate 2024-2025 (matches Prophet split, and the
  user's updated choice per the 2026-refreshed dataset). 2026 is YTD
  so excluded.

USAGE:
    python ml/train_rf.py                       # all 6 forecast-enabled diseases
    python ml/train_rf.py --disease DENGUE      # one disease only
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import pickle
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd
import mysql.connector
from dotenv import load_dotenv
from sklearn.ensemble import RandomForestClassifier
from sklearn.dummy import DummyClassifier
from sklearn.metrics import classification_report, confusion_matrix, f1_score

HERE = Path(__file__).resolve().parent
MODEL_DIR = HERE / "models"
REPORTS_DIR = HERE / "reports"

logging.basicConfig(
    level=os.getenv("ML_LOG_LEVEL", "info").upper(),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
log = logging.getLogger("hmap.rf")


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


def load_weekly_counts(conn, disease_id: int, year_start: int, year_end: int) -> pd.DataFrame:
    """All weekly Confirmed+Probable case counts per (barangay, year, week).

    Returns columns: barangay_id, year, week, cases.
    Includes a full grid of (barangay, year, week) so zero-weeks are explicit.
    """
    cur = conn.cursor()
    cur.execute(
        """SELECT barangay_id, morbidity_year, morbidity_week, COUNT(*) AS cases
             FROM cases
            WHERE disease_id = %s
              AND case_classification IN ('Confirmed','Probable')
              AND morbidity_year BETWEEN %s AND %s
              AND status_flag = 'Active'
            GROUP BY barangay_id, morbidity_year, morbidity_week""",
        (disease_id, year_start, year_end),
    )
    observed = pd.DataFrame(cur.fetchall(), columns=["barangay_id", "year", "week", "cases"])

    # Build the full grid so zero-weeks exist
    cur.execute("SELECT barangay_id FROM barangays ORDER BY barangay_id")
    barangay_ids = [r[0] for r in cur.fetchall()]
    grid = pd.MultiIndex.from_product(
        [barangay_ids, range(year_start, year_end + 1), range(1, 54)],
        names=["barangay_id", "year", "week"],
    ).to_frame(index=False)
    df = grid.merge(observed, on=["barangay_id", "year", "week"], how="left").fillna({"cases": 0})
    df["cases"] = df["cases"].astype(int)
    return df


# ─── Feature engineering ─────────────────────────────────────────────────────

def build_features_and_labels(weekly: pd.DataFrame, year_start: int) -> pd.DataFrame:
    """Return one row per (barangay, year, week) with the 8 Ch.3 features + 'risk' label.

    Only rows with year >= year_start + 5 are returned, because the prior-5-years
    baseline doesn't exist for earlier weeks (and we can't label them honestly).
    """
    rows = []
    # Index by (barangay, year, week) for fast lookup
    idx = weekly.set_index(["barangay_id", "year", "week"])["cases"]
    barangays = sorted(weekly["barangay_id"].unique())
    years = sorted(weekly["year"].unique())

    for year in years:
        if year < year_start + 5:
            continue  # not enough baseline yet
        baseline_years = list(range(year - 5, year))
        for week in range(1, 54):
            # 5-year baseline mean for this (week) across barangays?
            # Ch.3 says "five-year historical mean" as a barangay-level feature, so
            # we compute per-barangay 5-year mean.
            for bid in barangays:
                try:
                    current = int(idx.loc[(bid, year, week)])
                except KeyError:
                    current = 0
                # Same-week-prior-year
                try:
                    prior_yr = int(idx.loc[(bid, year - 1, week)])
                except KeyError:
                    prior_yr = 0
                # 5-year baseline for this (bid, week)
                baseline_counts = []
                for by in baseline_years:
                    try:
                        baseline_counts.append(int(idx.loc[(bid, by, week)]))
                    except KeyError:
                        baseline_counts.append(0)
                mean_5yr = float(np.mean(baseline_counts))
                std_5yr = float(np.std(baseline_counts, ddof=1)) if len(baseline_counts) > 1 else 0.0
                threshold = mean_5yr + 2 * std_5yr
                ratio = current / mean_5yr if mean_5yr > 0 else (1.0 if current == 0 else float("inf"))

                # Cumulative YTD = sum of weeks 1..week of this year for this barangay
                ytd = 0
                for w in range(1, week + 1):
                    try:
                        ytd += int(idx.loc[(bid, year, w)])
                    except KeyError:
                        pass

                # Risk label
                if current > threshold:
                    risk = "High"
                elif current > mean_5yr:
                    risk = "Moderate"
                else:
                    risk = "Low"

                # Calendar month: real month of the ISO week's Monday
                try:
                    month = pd.Timestamp.fromisocalendar(year, min(week, 53), 1).month
                except ValueError:
                    month = pd.Timestamp.fromisocalendar(year, 52, 1).month

                rows.append({
                    "barangay_id": bid,
                    "year": year,
                    "week": week,
                    "morbidity_week": week,
                    "calendar_month": month,
                    "current_cases": current,
                    "prior_year_cases": prior_yr,
                    "mean_5yr": mean_5yr,
                    "ratio_to_mean": min(ratio, 100.0),  # clip the divide-by-zero case
                    "ytd_cases": ytd,
                    "risk": risk,
                })
    return pd.DataFrame(rows)


FEATURE_COLS = [
    "barangay_id",
    "morbidity_week",
    "calendar_month",
    "current_cases",
    "prior_year_cases",
    "mean_5yr",
    "ratio_to_mean",
    "ytd_cases",
]


# ─── Train + validate ───────────────────────────────────────────────────────

@dataclass
class TrainResult:
    disease_code: str
    n_train: int
    n_test: int
    accuracy: float | None
    macro_f1: float | None
    class_report: dict | None
    confusion: list[list[int]] | None
    feature_importance: dict[str, float]
    label_distribution_train: dict
    label_distribution_test: dict
    baseline_accuracy: float | None
    baseline_macro_f1: float | None
    baseline_class_report: dict | None
    model_path: Path


def train_one(disease_id: int, disease_code: str, conn, args) -> TrainResult | None:
    log.info("loading weekly counts for %s", disease_code)
    weekly = load_weekly_counts(conn, disease_id, args.year_start, args.holdout_end)
    if weekly["cases"].sum() == 0:
        log.warning("skip %s — zero Confirmed+Probable cases in range", disease_code)
        return None

    log.info("building features + labels for %s", disease_code)
    df = build_features_and_labels(weekly, args.year_start)
    if df.empty:
        log.warning("skip %s — no labeled rows produced", disease_code)
        return None

    train_df = df[df["year"] <= args.train_end].copy()
    test_df = df[(df["year"] >= args.holdout_start) & (df["year"] <= args.holdout_end)].copy()

    if len(train_df) == 0:
        log.warning("skip %s — empty training set", disease_code)
        return None

    X_train = train_df[FEATURE_COLS].values
    y_train = train_df["risk"].values
    X_test = test_df[FEATURE_COLS].values
    y_test = test_df["risk"].values

    clf = RandomForestClassifier(
        n_estimators=200,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1,
    )
    clf.fit(X_train, y_train)

    # Evaluate
    if len(X_test) > 0:
        y_pred = clf.predict(X_test)
        accuracy = float((y_pred == y_test).mean())
        macro_f1 = float(f1_score(y_test, y_pred, average="macro", zero_division=0))
        report = classification_report(y_test, y_pred, output_dict=True, zero_division=0)
        labels_in_test = sorted(set(y_test) | set(y_pred))
        confusion = confusion_matrix(y_test, y_pred, labels=labels_in_test).tolist()
        confusion_labels = labels_in_test

        # Majority-class baseline — every row predicted as the most common
        # training label. If RF doesn't beat this, the "model" is just
        # exploiting class imbalance (most weeks have zero cases → Low).
        dummy = DummyClassifier(strategy="most_frequent")
        dummy.fit(X_train, y_train)
        y_base = dummy.predict(X_test)
        baseline_accuracy = float((y_base == y_test).mean())
        baseline_macro_f1 = float(f1_score(y_test, y_base, average="macro", zero_division=0))
        baseline_report = classification_report(y_test, y_base, output_dict=True, zero_division=0)
    else:
        accuracy = None
        macro_f1 = None
        report = None
        confusion = None
        confusion_labels = []
        baseline_accuracy = None
        baseline_macro_f1 = None
        baseline_report = None

    feature_importance = {
        name: float(imp) for name, imp in zip(FEATURE_COLS, clf.feature_importances_)
    }

    MODEL_DIR.mkdir(exist_ok=True)
    path = MODEL_DIR / f"rf_{disease_code}.pkl"
    with open(path, "wb") as f:
        pickle.dump(
            {
                "model": clf,
                "disease_code": disease_code,
                "feature_cols": FEATURE_COLS,
                "training_window": (args.year_start, args.train_end),
                "validation_holdout": (args.holdout_start, args.holdout_end),
                "accuracy": accuracy,
                "macro_f1": macro_f1,
                "classification_report": report,
                "confusion_matrix": confusion,
                "confusion_labels": confusion_labels,
                "feature_importance": feature_importance,
                "baseline_accuracy": baseline_accuracy,
                "baseline_macro_f1": baseline_macro_f1,
                "baseline_classification_report": baseline_report,
            },
            f,
        )

    return TrainResult(
        disease_code=disease_code,
        n_train=len(X_train),
        n_test=len(X_test),
        accuracy=accuracy,
        macro_f1=macro_f1,
        class_report=report,
        confusion=confusion,
        feature_importance=feature_importance,
        label_distribution_train=dict(pd.Series(y_train).value_counts()),
        label_distribution_test=dict(pd.Series(y_test).value_counts()) if len(y_test) > 0 else {},
        baseline_accuracy=baseline_accuracy,
        baseline_macro_f1=baseline_macro_f1,
        baseline_class_report=baseline_report,
        model_path=path,
    )


def report(results: list[TrainResult]) -> None:
    bar = "=" * 78
    print()
    print(bar)
    print("  Random Forest training results")
    print(bar)
    for r in results:
        print()
        print(f"  Disease: {r.disease_code}    n_train={r.n_train:,}  n_test={r.n_test:,}")
        print(f"    Train label distribution: {dict(r.label_distribution_train)}")
        print(f"    Test  label distribution: {dict(r.label_distribution_test)}")
        if r.accuracy is not None:
            lift_acc = (r.accuracy - (r.baseline_accuracy or 0)) * 100
            lift_f1 = ((r.macro_f1 or 0) - (r.baseline_macro_f1 or 0))
            print(f"    RF     :  accuracy={r.accuracy:.3f}  macro-F1={r.macro_f1:.3f}")
            print(f"    Baseline: accuracy={r.baseline_accuracy:.3f}  macro-F1={r.baseline_macro_f1:.3f}  (majority-class)")
            print(f"    Lift   :  +{lift_acc:.1f}pp accuracy  +{lift_f1:.3f} macro-F1")
        if r.class_report:
            print(f"    Per-class metrics (precision/recall/F1):")
            for cls in ("Low", "Moderate", "High"):
                m = r.class_report.get(cls)
                if m:
                    print(f"      {cls:<10} P={m['precision']:.3f}  R={m['recall']:.3f}  F1={m['f1-score']:.3f}  support={int(m['support'])}")
        if r.confusion:
            print(f"    Confusion matrix:")
            print(f"      {r.confusion}")
        print(f"    Top features: ", end="")
        top = sorted(r.feature_importance.items(), key=lambda kv: kv[1], reverse=True)[:4]
        print(", ".join(f"{k}={v:.3f}" for k, v in top))
    print()
    print(bar)
    print(f"  {len(results)} models written to {MODEL_DIR}")
    print(bar)


def write_reports(results: list[TrainResult], args) -> None:
    """Persist evaluation metrics to ml/reports/ for slides / thesis appendix."""
    if not results:
        return
    REPORTS_DIR.mkdir(exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    summary = {
        "generated_at_utc": ts,
        "training_window": [args.year_start, args.train_end],
        "validation_holdout": [args.holdout_start, args.holdout_end],
        "n_estimators": 200,
        "class_weight": "balanced",
        "baseline_strategy": "most_frequent",
        "models": [
            {
                "disease_code": r.disease_code,
                "n_train": r.n_train,
                "n_test": r.n_test,
                "accuracy": r.accuracy,
                "macro_f1": r.macro_f1,
                "baseline_accuracy": r.baseline_accuracy,
                "baseline_macro_f1": r.baseline_macro_f1,
                "lift_accuracy_pp": (r.accuracy - r.baseline_accuracy) * 100
                    if r.accuracy is not None and r.baseline_accuracy is not None else None,
                "lift_macro_f1": (r.macro_f1 - r.baseline_macro_f1)
                    if r.macro_f1 is not None and r.baseline_macro_f1 is not None else None,
                "label_distribution_train": {str(k): int(v) for k, v in r.label_distribution_train.items()},
                "label_distribution_test": {str(k): int(v) for k, v in r.label_distribution_test.items()},
                "classification_report": r.class_report,
                "baseline_classification_report": r.baseline_class_report,
                "confusion_matrix": r.confusion,
                "feature_importance": r.feature_importance,
            }
            for r in results
        ],
    }
    json_path = REPORTS_DIR / f"rf_eval_{ts}.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    csv_path = REPORTS_DIR / f"rf_eval_{ts}.csv"
    with open(csv_path, "w", encoding="utf-8") as f:
        f.write("disease,n_train,n_test,rf_accuracy,baseline_accuracy,lift_acc_pp,rf_macro_f1,baseline_macro_f1,lift_macro_f1\n")
        for r in results:
            f.write(f"{r.disease_code},{r.n_train},{r.n_test},"
                    f"{r.accuracy:.4f},{r.baseline_accuracy:.4f},"
                    f"{(r.accuracy - r.baseline_accuracy)*100:.2f},"
                    f"{r.macro_f1:.4f},{r.baseline_macro_f1:.4f},"
                    f"{r.macro_f1 - r.baseline_macro_f1:.4f}\n")

    # Stable "latest" pointer
    latest_json = REPORTS_DIR / "rf_eval_latest.json"
    latest_csv = REPORTS_DIR / "rf_eval_latest.csv"
    latest_json.write_text(json_path.read_text(encoding="utf-8"), encoding="utf-8")
    latest_csv.write_text(csv_path.read_text(encoding="utf-8"), encoding="utf-8")
    print(f"  Eval report: {json_path.name}, {csv_path.name}")


# ─── Entry ──────────────────────────────────────────────────────────────────

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--year-start", type=int, default=2010)
    p.add_argument("--train-end", type=int, default=2023, help="Last year included in training")
    p.add_argument("--holdout-start", type=int, default=2024)
    p.add_argument("--holdout-end", type=int, default=2025)
    p.add_argument("--disease", default=None,
                   help="Train only this disease_code; default all forecast_enabled")
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
            r = train_one(disease_id, code, conn, args)
            if r:
                results.append(r)
    finally:
        conn.close()

    report(results)
    write_reports(results, args)


if __name__ == "__main__":
    main()
