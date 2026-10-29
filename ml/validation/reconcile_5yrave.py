"""Ch.4 Level 2 data fidelity: the system's Weekly Report vs the CESU PIDSR workbook.

Compares, for every disease present in both and every morbidity week 1-52:
  - the five-year average of year-to-date cases (system avg_5yr_cases vs the
    workbook 5YrAve "Average" column) — pass criterion: within 1% (Table 4)
  - year-to-date cases of the current and prior year (system cases_current /
    cases_prior vs the workbook's 2026 / 2025 columns)

Inputs:
  cesu.csv     ml/validation/export_5yrave_weeks.ps1 (the workbook's own formulas)
  system.json  laravel/tests/dump_weekly_summary.php (GET /api/weekly-summary)

    python ml/validation/reconcile_5yrave.py cesu.csv system.json OUT_DIR

Writes OUT_DIR/reconciliation_detail.csv (one row per disease-week) and
OUT_DIR/reconciliation_summary.md. Only aggregate counts are written.
"""
import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from etl_registry import DISEASE_MAP, norm_disease_key  # noqa: E402  same name mapping as the loader

TOLERANCE_PCT = 1.0


def code_for(workbook_name):
    m = DISEASE_MAP.get(norm_disease_key(workbook_name))
    return m[0] if m and m[2] else None


def pct_diff(system, cesu):
    if cesu == 0:
        return 0.0 if system == 0 else float("inf")
    return abs(system - cesu) / cesu * 100


def main(cesu_csv, system_json, out_dir):
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    sysdata = json.loads(Path(system_json).read_text(encoding="utf-8"))
    year = sysdata["year"]
    system = {}
    for w, payload in sysdata["weeks"].items():
        for r in payload["rows"]:
            system[(r["disease_code"], int(w))] = r

    detail, unmatched = [], set()
    with open(cesu_csv, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            code = code_for(row["disease"])
            week = int(row["week"])
            if code is None or (code, week) not in system:
                unmatched.add(row["disease"])
                continue
            s = system[(code, week)]
            c_avg = float(row["avg_cases"])
            c_cur = int(float(row[f"y{year}_cases"]))
            c_prior = int(float(row[f"y{year - 1}_cases"]))
            detail.append({
                "disease_code": code, "workbook_name": row["disease"], "week": week,
                "cesu_avg5": c_avg, "system_avg5": s["avg_5yr_cases"],
                "avg5_pct_diff": round(pct_diff(s["avg_5yr_cases"], c_avg), 3),
                "cesu_current": c_cur, "system_current": s["cases_current"],
                "cesu_prior": c_prior, "system_prior": s["cases_prior"],
            })

    with open(out / "reconciliation_detail.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(detail[0].keys()))
        w.writeheader()
        w.writerows(detail)

    by_code = {}
    for d in detail:
        by_code.setdefault(d["disease_code"], []).append(d)

    lines = [f"# Weekly Report vs CESU PIDSR workbook, {year} (weeks 1-52)", "",
             f"Baseline years {year - 5}-{year - 1}. Five-year average of year-to-date cases, all case "
             f"classifications, both sides. Pass = within {TOLERANCE_PCT:g}% of the workbook in every week.", "",
             "| Disease | Weeks | Avg exact | Avg within 1% | Max avg diff (cases) | Max % diff | "
             f"{year} YTD exact | {year - 1} YTD exact | Result |",
             "|---|---|---|---|---|---|---|---|---|"]
    tot = {"weeks": 0, "exact": 0, "within": 0}
    for code, rows in sorted(by_code.items(), key=lambda kv: -max(r["cesu_avg5"] for r in kv[1])):
        n = len(rows)
        exact = sum(1 for r in rows if abs(r["system_avg5"] - r["cesu_avg5"]) < 1e-9)
        within = sum(1 for r in rows if r["avg5_pct_diff"] <= TOLERANCE_PCT)
        max_abs = max(abs(r["system_avg5"] - r["cesu_avg5"]) for r in rows)
        finite = [r["avg5_pct_diff"] for r in rows if r["avg5_pct_diff"] != float("inf")]
        max_pct = max(finite) if finite else 0.0
        has_inf = any(r["avg5_pct_diff"] == float("inf") for r in rows)
        cur_exact = sum(1 for r in rows if r["system_current"] == r["cesu_current"])
        prior_exact = sum(1 for r in rows if r["system_prior"] == r["cesu_prior"])
        result = "Pass" if within == n else "Fail"
        lines.append(f"| {code} | {n} | {exact} | {within} | {max_abs:.2f} | "
                     f"{max_pct:.2f}{' (and 0 vs >0)' if has_inf else ''} | {cur_exact}/{n} | {prior_exact}/{n} | {result} |")
        tot["weeks"] += n
        tot["exact"] += exact
        tot["within"] += within
    lines += ["", f"Overall: {tot['within']} of {tot['weeks']} disease-weeks within {TOLERANCE_PCT:g}% "
              f"({tot['within'] / tot['weeks'] * 100:.1f}%); {tot['exact']} exact.",
              "", "Workbook diseases not compared (not alert-enabled in the system, or no mapping): "
              + (", ".join(sorted(unmatched)) or "none")]
    (out / "reconciliation_summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main(*sys.argv[1:4])
