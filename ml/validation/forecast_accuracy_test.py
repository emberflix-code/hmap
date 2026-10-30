"""Forecast accuracy on weeks withheld from the model (Chapter 4, Level 2).

For each served disease (DENGUE, TYP, LEP):

  Two-year test   train 2010-2023 with the dashboard settings, predict every
                  week of 2024-2025 at once; share of weeks inside the 80% band.
  Four-week test  every 4 weeks through 2024-2025, retrain on all weeks before
                  that week and predict the next 4 (how the dashboard is used);
                  average miss, MAPE, band coverage, and whether the direction of
                  the 4 weeks (vs the 4 before) was right. Compared with the
                  same-week-last-year guess.

Only aggregate weekly counts are read. Uses DB_HOST/DB_PORT/DB_USER/DB_PASSWORD/
DB_NAME like the ETL.

    python ml/validation/forecast_accuracy_test.py [OUT_DIR]
"""
import json
import logging
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import mysql.connector  # noqa: E402
from train_prophet import fit_prophet, mape, rmse, weekly_series  # noqa: E402

logging.getLogger("cmdstanpy").setLevel(logging.WARNING)
logging.getLogger("prophet").setLevel(logging.WARNING)

SEED = 2026
DISEASES = ("DENGUE", "TYP", "LEP")


def main(out_dir):
    cn = mysql.connector.connect(host=os.environ["DB_HOST"], port=int(os.getenv("DB_PORT", "3306")),
                                 user=os.environ["DB_USER"], password=os.environ["DB_PASSWORD"],
                                 database=os.getenv("DB_NAME", "hmap_db"))
    cur = cn.cursor()
    out = {"train_years": [2010, 2023], "test_years": [2024, 2025], "diseases": {}}
    for code in DISEASES:
        cur.execute("SELECT disease_id FROM diseases WHERE disease_code=%s", (code,))
        did = cur.fetchone()[0]
        s = weekly_series(cn, did, None, 2010, 2025)
        test_mask = s["ds"].dt.year >= 2024
        train, test = s[~test_mask], s[test_mask]
        idx = s.set_index("ds")["y"]

        np.random.seed(SEED)
        m = fit_prophet(train)
        fc = m.predict(m.make_future_dataframe(periods=len(test), freq="W-MON", include_history=False)).iloc[:len(test)]
        a = test["y"].values
        two_year = {
            "mape": mape(a, fc["yhat"].values), "rmse": rmse(a, fc["yhat"].values),
            "coverage80": float(((a >= fc["yhat_lower"].values) & (a <= fc["yhat_upper"].values)).mean()),
            "actual_peak_2024": float(a[:52].max()), "forecast_peak_2024": float(fc["yhat"].values[:52].max()),
        }

        rows, starts = [], list(range(0, len(test), 4))
        for k in starts:
            origin = test["ds"].iloc[k]
            np.random.seed(SEED)
            mm = fit_prophet(s[s["ds"] < origin])
            f = mm.predict(mm.make_future_dataframe(periods=4, freq="W-MON", include_history=False))
            for h in range(min(4, len(test) - k)):
                d = test["ds"].iloc[k + h]
                rows.append({"k": k, "h": h + 1, "actual": float(test["y"].iloc[k + h]),
                             "yhat": float(f["yhat"].iloc[h]), "lo": float(f["yhat_lower"].iloc[h]),
                             "hi": float(f["yhat_upper"].iloc[h]),
                             "naive": float(idx.get(d - pd.Timedelta(weeks=52), np.nan))})
        r = pd.DataFrame(rows)
        hits = []
        for k in starts:
            blk = r[r["k"] == k]
            if len(blk) < 4:
                continue
            prev = s[s["ds"] < test["ds"].iloc[k]].tail(4)["y"].sum()
            hits.append(bool(np.sign(blk["actual"].sum() - prev) == np.sign(blk["yhat"].sum() - prev)))
        four_week = {
            "n_forecasts": len(starts), "n_weeks": len(r),
            "mae": float((r["actual"] - r["yhat"]).abs().mean()),
            "naive_mae": float((r["actual"] - r["naive"]).abs().mean()),
            "mape": mape(r["actual"], r["yhat"]), "naive_mape": mape(r["actual"], r["naive"]),
            "coverage80": float(((r["actual"] >= r["lo"]) & (r["actual"] <= r["hi"])).mean()),
            "direction_correct": int(sum(hits)), "direction_n": len(hits),
            "mape_1wk": mape(r[r["h"] == 1]["actual"], r[r["h"] == 1]["yhat"]),
            "mape_4wk": mape(r[r["h"] == 4]["actual"], r[r["h"] == 4]["yhat"]),
            "weekly_mean": float(a.mean()), "weekly_min": float(a.min()), "weekly_max": float(a.max()),
        }
        out["diseases"][code] = {"two_year": two_year, "four_week": four_week}
        print(code, {k: round(v, 2) if isinstance(v, float) else v for k, v in four_week.items()})

    Path(out_dir).mkdir(parents=True, exist_ok=True)
    (Path(out_dir) / "forecast_accuracy.json").write_text(json.dumps(out, indent=2))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else str(Path(__file__).resolve().parents[2] / "docs" / "Chapter4_5" / "results"))
