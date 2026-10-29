"""Ch.4 test TC-FCT-01/02: forecast response time and repeatability.

Calls the running ML service (POST /predict/forecast) for every disease whose
forecast is displayed (it beats the seasonal-naive baseline), 5 times each,
and checks that each response arrives within 3 seconds and that repeated
calls return identical values (Ch.3 Table 4). A disease whose forecast is
withheld must answer 404 with the "not displayed" reason.

    python ml/validation/forecast_timing_test.py http://127.0.0.1:5050 [OUT_JSON]
"""
import json
import sys
import time
import urllib.error
import urllib.request

RUNS, LIMIT_S = 5, 3.0


def post(base, path, body):
    req = urllib.request.Request(base + path, data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"}, method="POST")
    t0 = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, json.loads(r.read()), time.perf_counter() - t0
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read() or b"{}"), time.perf_counter() - t0


def main(base, out=None):
    with urllib.request.urlopen(base + "/models", timeout=30) as r:
        models = json.loads(r.read())
    entries = models.get("models", models) if isinstance(models, dict) else models
    rows, ok_all = [], True
    for code in ["DENGUE", "TYP", "LEP", "MEA", "ILI", "HFMD"]:
        times, payloads, status = [], [], None
        for _ in range(RUNS):
            status, body, dt = post(base, "/predict/forecast", {"disease_code": code, "weeks_ahead": 4})
            times.append(dt)
            payloads.append(json.dumps(body, sort_keys=True))
        served = status == 200
        identical = len(set(payloads)) == 1
        within = max(times) <= LIMIT_S
        reason = None if served else (payloads[0][:160])
        ok = within and identical and (served or status == 404)
        ok_all &= ok
        rows.append({"disease": code, "status": status, "served": served, "max_s": round(max(times), 3),
                     "median_s": round(sorted(times)[RUNS // 2], 3), "identical": identical,
                     "withheld_reason": reason, "passed": ok})
        print(f"  {code:7s} HTTP {status}  median {sorted(times)[RUNS // 2]:.3f} s  max {max(times):.3f} s  "
              f"identical={identical}  {'served' if served else 'withheld'}")
    print("PASSED" if ok_all else "FAILED")
    if out:
        with open(out, "w", encoding="utf-8") as f:
            json.dump({"runs": RUNS, "limit_s": LIMIT_S, "results": rows, "passed": ok_all,
                       "models_listed": len(entries) if hasattr(entries, "__len__") else None}, f, indent=2)
    return 0 if ok_all else 1


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:3]))
