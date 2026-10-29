"""Ch.4 Level 2 hotspot detection test: planted clusters with known answers.

Runs the production detector (detect_clusters.run_detection, CESU rule:
200 m, 3 cases, 4 weeks) on a synthetic dengue dataset (fixed seed, no real
patient data) that contains:

  should be detected
    P1-P3   compact clusters (3-5 cases within 100 m, same week)
    P4      a growing cluster (6 cases within 100 m over two weeks)
    P5      a cross-barangay cluster (4 cases within 150 m, two barangays)
  must NOT be detected
    N1      3 cases 250 m apart in the same week (too far apart)
    N2      3 cases within 50 m but about a month apart (too slow for 4 weeks)
    N3      only 2 cases close together (below the 3-case minimum)
    noise   background cases at least 400 m from every other case

Pass criteria (Ch.3 Table 4): every planted cluster detected, no spurious
cluster (no detected cluster contains a case outside P1-P5), identical
results on repeated runs (also with the input order shuffled).

    python ml/validation/planted_clusters_test.py [OUT_DIR]
"""
import json
import math
import random
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from detect_clusters import haversine_m, run_detection  # noqa: E402

EPS_M, MIN_CASES, WEEKS = 200.0, 3, 4
SEED = 20261030
ORIGIN = (14.4793, 121.0198)   # Paranaque City
M_PER_DEG_LAT = 111_320.0


def offset(lat, lng, north_m, east_m):
    return (lat + north_m / M_PER_DEG_LAT,
            lng + east_m / (M_PER_DEG_LAT * math.cos(math.radians(lat))))


def build(rng):
    cases, truth = [], {}
    next_id = [1]

    def add(group, lat, lng, d, barangay):
        cid = next_id[0]
        next_id[0] += 1
        cases.append({"case_id": cid, "case_date": d, "lat": lat, "lng": lng, "barangay": barangay})
        truth.setdefault(group, []).append(cid)

    def compact(group, centre, n, radius_m, dates, barangays):
        for i in range(n):
            ang, r = rng.uniform(0, 2 * math.pi), radius_m * math.sqrt(rng.random())
            lat, lng = offset(*centre, r * math.sin(ang), r * math.cos(ang))
            add(group, lat, lng, dates[i % len(dates)], barangays[i % len(barangays)])

    wk = lambda n: date(2025, 1, 2) + timedelta(weeks=n)   # Thursdays of 2025
    compact("P1", offset(*ORIGIN, 0, 0), 3, 80, [wk(5)], ["San Dionisio"])
    compact("P2", offset(*ORIGIN, 1500, 1500), 4, 90, [wk(12)], ["San Antonio"])
    compact("P3", offset(*ORIGIN, -1500, 1500), 5, 100, [wk(20)], ["Marcelo Green Village"])
    compact("P4", offset(*ORIGIN, 3000, 0), 6, 100, [wk(30), wk(30) + timedelta(days=4), wk(31)], ["Baclaran"])
    compact("P5", offset(*ORIGIN, -3000, 0), 4, 75, [wk(40)], ["Don Bosco", "Merville"])

    n1 = offset(*ORIGIN, 1500, -1500)
    for k in range(3):   # a straight line, 250 m between neighbours
        add("N1", *offset(*n1, 0, 250 * k), wk(8), "Tambo")
    n2 = offset(*ORIGIN, -1500, -1500)
    for k in range(3):   # same spot, 31 days apart
        add("N2", *offset(*n2, 10 * k, 0), wk(15) + timedelta(days=31 * k), "Sun Valley")
    n3 = offset(*ORIGIN, 4500, 1500)
    for k in range(2):
        add("N3", *offset(*n3, 20 * k, 0), wk(25), "La Huerta")

    # Background: random cases at least 400 m from every case placed so far
    placed = 0
    while placed < 120:
        lat, lng = offset(*ORIGIN, rng.uniform(-6000, 6000), rng.uniform(-4000, 4000))
        if all(haversine_m(lat, lng, c["lat"], c["lng"]) >= 400 for c in cases):
            add("noise", lat, lng, wk(rng.randrange(0, 50)) + timedelta(days=rng.randrange(0, 7)), "Various")
            placed += 1
    cases.sort(key=lambda c: c["case_date"])
    return cases, truth


def evaluate(clusters, truth):
    planted = {g: set(ids) for g, ids in truth.items() if g.startswith("P")}
    planted_ids = set().union(*planted.values())
    found, spurious = {g: [] for g in planted}, []
    for c in clusters:
        members = set(c["case_ids"])
        if not members <= planted_ids:
            spurious.append(sorted(members))
            continue
        owners = [g for g, ids in planted.items() if members & ids]
        if len(owners) != 1:
            spurious.append(sorted(members))
            continue
        found[owners[0]].append(c)
    return found, spurious


def main(out_dir=None):
    rng = random.Random(SEED)
    cases, truth = build(rng)
    clusters = run_detection(cases, EPS_M, MIN_CASES, WEEKS)
    found, spurious = evaluate(clusters, truth)

    repeat_ok = True
    reference = sorted(c["fingerprint"] for c in clusters)
    for k in range(3):
        shuffled = cases[:]
        random.Random(k).shuffle(shuffled)
        shuffled.sort(key=lambda c: c["case_date"])   # the loader sorts by date; order within a date varies
        again = sorted(c["fingerprint"] for c in run_detection(shuffled, EPS_M, MIN_CASES, WEEKS))
        repeat_ok &= again == reference

    rows = []
    for g in sorted(found):
        full = set(truth[g])
        snaps = found[g]
        complete = any(set(c["case_ids"]) == full for c in snaps)
        bgys = sorted({b for c in snaps for b in c["barangays"]})
        rows.append({"group": g, "planted_cases": len(full), "detected_snapshots": len(snaps),
                     "full_cluster_detected": complete, "barangays": bgys,
                     "max_radius_m": round(max((c["radius_m"] for c in snaps), default=0), 1)})
    negatives_clear = not any(set(c["case_ids"]) & set(truth[g]) for g in ("N1", "N2", "N3", "noise") for c in clusters)

    result = {
        "parameters": {"eps_m": EPS_M, "min_cases": MIN_CASES, "window_weeks": WEEKS, "seed": SEED},
        "total_cases": len(cases), "clusters_detected": len(clusters),
        "planted": rows, "spurious_clusters": spurious,
        "negatives_clear": negatives_clear, "repeat_runs_identical": repeat_ok,
        "passed": all(r["full_cluster_detected"] for r in rows) and not spurious and negatives_clear and repeat_ok,
    }

    print(f"{len(cases)} synthetic cases, {len(clusters)} clusters detected")
    for r in rows:
        print(f"  {r['group']}: {r['planted_cases']} planted, full cluster detected={r['full_cluster_detected']}, "
              f"snapshots={r['detected_snapshots']}, radius<={r['max_radius_m']} m, barangays={', '.join(r['barangays'])}")
    print(f"  near-misses and noise clear: {negatives_clear}")
    print(f"  spurious clusters: {len(spurious)}")
    print(f"  repeated runs identical: {repeat_ok}")
    print("PASSED" if result["passed"] else "FAILED")
    if out_dir:
        Path(out_dir).mkdir(parents=True, exist_ok=True)
        (Path(out_dir) / "planted_clusters_result.json").write_text(json.dumps(result, indent=2, default=str))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:2]))
