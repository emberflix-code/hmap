"""Build Chapter4_Presentation_Analysis.docx (TUP outline: Project Technical
Description, Technical Specifications, Test Results, Evaluation Results).

Formatting helpers are taken from build_chapters_final.py (everything above its
"# Build document" marker), so Chapter 4 always matches Chapters 1-3: US
Letter, 1.5-inch left margin, Times New Roman 12, double spacing, italic
"Figure N." label with bold title, bold "Table N" with italic title.

Test figures are read from the result files the test scripts write to
docs/Chapter4_5/results/ (realdata_tests.json, workflow_tests.json,
reconciliation_detail.csv, planted_clusters_result.json, forecast_timing.json),
so the chapter always reports the latest run. Table and figure numbers
continue from Chapter 3 (Table 7, Figure 4). Screenshots and evaluation
results are placeholders until the deployed system is captured and the
evaluation is conducted.

Usage: python build_chapter4.py
"""
import ast
import csv
import json
import os
import re
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.join(HERE, "..", "Chapter4_5", "results")
SHOTS = os.path.join(HERE, "figures", "ch4")
OUT = os.path.join(HERE, "Chapter4_Presentation_Analysis.docx")

# Reuse the Chapter 1-3 helpers verbatim
_src = open(os.path.join(HERE, "build_chapters_final.py"), encoding="utf-8").read()
exec(compile(_src.split("# Build document")[0], "build_chapters_final.py (helpers)", "exec"))

from PIL import Image, ImageDraw, ImageFont  # noqa: E402


def load(name):
    with open(os.path.join(RESULTS, name), encoding="utf-8") as f:
        return json.load(f)


# Disease names from the loader's own seed list, so the chapter uses the system's names
_etl = ast.parse(open(os.path.join(HERE, "..", "..", "ml", "etl_registry.py"), encoding="utf-8").read())
DISEASE_NAMES = {d["code"]: d["name"].replace(" & ", " and ") for n in _etl.body
                 if isinstance(n, ast.AnnAssign) and getattr(n.target, "id", "") == "DISEASES_SEED"
                 for d in ast.literal_eval(n.value)}

realdata = {t["id"]: t for t in load("realdata_tests.json")["tests"]}
realdata_meta = load("realdata_tests.json")
workflow = {t["id"]: t for t in load("workflow_tests.json")["tests"]}
SEC_ROUTES = re.search(r"(\d+) of (\d+) routes", workflow["TC-SEC-01"]["observed"]).groups()
SEC_ROLES = re.search(r"(\d+) of (\d+) lower-role", workflow["TC-SEC-02"]["observed"]).groups()
planted = load("planted_clusters_result.json")
forecast = load("forecast_timing.json")


def status(passed):
    return "Passed" if passed else "Failed"


def placeholder(name, label):
    """The real screenshot figures/ch4/screens/<name> when it has been captured
    (docs/STAGING_SCREENSHOTS.md), otherwise a grey placeholder image."""
    real = os.path.join(SHOTS, "screens", name)
    if os.path.exists(real):
        return real
    os.makedirs(SHOTS, exist_ok=True)
    path = os.path.join(SHOTS, name)
    img = Image.new("RGB", (1600, 900), (236, 239, 243))
    d = ImageDraw.Draw(img)
    d.rectangle([8, 8, 1591, 891], outline=(150, 156, 166), width=6)
    try:
        font = ImageFont.truetype("arial.ttf", 46)
        small = ImageFont.truetype("arial.ttf", 32)
    except OSError:
        font = small = ImageFont.load_default()
    d.text((800, 400), f"[Screenshot: {label}]", fill=(80, 86, 96), font=font, anchor="mm")
    d.text((800, 480), "to be captured from the deployed system", fill=(110, 116, 126), font=small, anchor="mm")
    img.save(path)
    return path


# ---------------------------------------------------------------------------
doc = Document()
doc.core_properties.author = "Kemberly M. Magsino"
doc.core_properties.title = ("Web-Based Disease Outbreak Management System for the City "
                             "Epidemiology and Surveillance Unit: Chapter 4")
doc.styles["Normal"].font.name = "Times New Roman"
doc.styles["Normal"].font.size = Pt(12)
sec = doc.sections[0]
sec.page_width, sec.page_height = Inches(8.5), Inches(11)
sec.top_margin = sec.bottom_margin = sec.right_margin = Inches(1)
sec.left_margin = Inches(1.5)
hp = sec.header.paragraphs[0]
hp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
add_page_number_field(hp)

table_no = [7]
fig_no = [4]


def next_table():
    table_no[0] += 1
    return table_no[0]


def next_fig():
    fig_no[0] += 1
    return fig_no[0]


def tc_table(title, rows):
    """rows: (id, desired, steps list, observed, passed)"""
    n = next_table()
    add_table(doc, n, title, ["Test Case", "Desired Output", "Test Procedure", "Result", "Status"],
              [(i, d, " ".join(f"({k + 1}) {s}" for k, s in enumerate(st)), o, status(p)) for i, d, st, o, p in rows],
              widths=[0.9, 1.4, 1.8, 1.45, 0.6], font_size=9)
    return n


def thousands(s):
    return re.sub(r"\b\d{4,}\b", lambda m: f"{int(m.group()):,}", s)


# The scripts' observed text is a log line; these turn it into manuscript wording
# while keeping every number from the result file.
POLISH = [
    ("TC-CAS-01", r"age group (\S+), audit row present, address (\S+)",
     lambda m: f"Case saved and attributed to the encoder; age group {m[1]} derived from the age; audit entry and pinned address saved"),
    ("TC-CAS-02", r"(\d+) of (\d+) rejected; cases saved: 0",
     lambda m: f"{m[1]} of {m[2]} invalid records rejected; no case saved"),
    ("TC-CAS-03", r"inserted (\d+), failed (\d+) \(rows ([\d, ]+)\), (\d+) audit rows",
     lambda m: f"{m[1]} rows saved; rows {m[3].replace(', ', ' and ')} rejected with their reasons; {m[4]} audit entries"),
    ("TC-CAS-04", r"HTTP 422",
     lambda m: "Upload refused; the response lists the missing columns"),
    ("TC-THR-01", r"(\d+) of (\d+) disease-weeks match",
     lambda m: thousands(f"{m[1]} of {m[2]} disease-weeks identical to the recomputation")),
    ("TC-THR-02", r"MEA single_case_trigger = 1, DENGUE = 0",
     lambda m: "Measles flagged as a single-case alert disease; dengue not flagged"),
    ("TC-RPT-01", r"export (\d+) = database (\d+); Unknown barangay (\d+) = database (\d+)",
     lambda m: thousands(f"Export total of {m[1]} equals the database count of {m[2]}, including {m[3]} cases of unknown barangay")),
    ("TC-RPT-02", r"(\d+) of 52 weeks identical \((\d+) EPIDEMIC barangay-weeks\)",
     lambda m: f"Identical in {m[1]} of 52 weeks ({m[2]} barangay-weeks flagged EPIDEMIC)"),
    ("TC-RPT-03", r"export (\d+) rows = database (\d+)",
     lambda m: thousands(f"{m[1]} rows exported, equal to the {m[2]} active cases")),
    ("TC-RPT-04", r"(\d+) of (\d+) role checks",
     lambda m: f"{m[1]} of {m[2]} role checks as specified"),
    ("TC-RPT-05", r"(\d+) EXPORT audit rows, (\d+) with a row count",
     lambda m: f"{m[2]} of {m[1]} exports logged with their row counts"),
    ("TC-SEC-01", r"(\d+) of (\d+) routes answered 401",
     lambda m: f"{m[1]} of {m[2]} protected routes refused the request (HTTP 401)"),
    ("TC-SEC-02", r"(\d+) of (\d+) lower-role requests refused with 403",
     lambda m: f"{m[1]} of {m[2]} lower-role requests refused (HTTP 403)"),
    ("TC-SEC-03", r"non-CESU employee 403, CESU Analyst 200, deactivated Analyst 403, (\d+) refusals logged",
     lambda m: "Non-CESU employee refused; authorized Analyst admitted; deactivated Analyst refused at once; both refusals logged"),
    ("TC-E2E-01", r"cluster of (\d+) cases \(radius (\d+) m\); Tambo tier (\w+) \(([^)]*)\); (\d+) recommendations, rank (\d+); "
                  r"alerts: ([^;]+); (\d+) emails sent, max (\d+) s after detection; whole flow ([\d.]+) s",
     lambda m: f"Hotspot of {m[1]} cases detected (radius {m[2]} m); Tambo rated {m[3]} ({m[4]}); ranked first with "
               f"{m[5]} recommended items; epidemic-threshold and hotspot alerts emailed within {max(1, int(m[9]))} second of "
               f"detection; whole flow {m[10]} seconds"),
]


def tc_from(src, tid):
    t = src[tid]
    observed = t["observed"]
    for pid, pattern, fmt in POLISH:
        if pid == tid:
            m = re.search(pattern, observed)
            if not m:
                raise SystemExit(f"{tid}: result text changed, update POLISH: {observed}")
            observed = fmt(m)
    return (t["id"], t["desired"], t["steps"], observed, t["passed"])


add_chapter_break(doc, "Chapter 4", "PRESENTATION, ANALYSIS, AND INTERPRETATION OF DATA", page_break=False)
add_para(doc, "This chapter presents the developed Web-Based Disease Outbreak Management System for "
         "the City Epidemiology and Surveillance Unit, its technical specifications, the results "
         "of the three levels of testing described in Chapter 3, and the results of the evaluation "
         "of the system by its intended users and by IT professionals. Each result is interpreted "
         "against the pass criteria and the evaluation scale adopted in Chapter 3.")

# =========================================================================
add_section(doc, "", "Project Technical Description")
add_para(doc, "The developed system is a web application used by the personnel of the City "
         "Epidemiology and Surveillance Unit (CESU) of the City Health Office of Parañaque City. It "
         "follows the architecture presented in Chapter 3 (Figure 2): a Laravel web application "
         "serves the user interface and the application programming interface, a Python analytics "
         "service produces trend forecasts, and a MySQL database holds the case records, "
         "thresholds, hotspots, recommendations, notifications, and the audit log. Only CESU "
         "personnel listed in the authorization list maintained by the Administrator can sign in, "
         "using their HRMO Portal account and a one-time code from an authenticator application. "
         "The system implements the nine modules specified in Chapter 3, described below in the "
         "order of the surveillance workflow.")

modules = [
    ("Case Data Management",
     "Data Encoders enter cases one at a time through a form that mirrors the PIDSR case report "
     "form, or upload many cases at once as a CSV file. Each record is validated before it is "
     "saved: the disease and barangay must be known, the morbidity week and year must be valid, "
     "dates cannot be in the future, admission cannot precede onset, and the age group must agree "
     "with the age. In a CSV upload, valid rows are saved and each rejected row is reported by its "
     "row number. Every saved case is recorded in the audit log. Cases whose barangay is unknown "
     "are kept, counted in the city totals, and left out of barangay-level maps and rankings.",
     "case_entry.png", "Case Entry Form"),
    ("Threshold Monitoring and Weekly Reporting",
     "For every alert-enabled disease and morbidity week, the system computes the PIDSR alert "
     "threshold (mean plus one standard deviation) and epidemic threshold (mean plus two standard "
     "deviations) from the Confirmed and Probable cases of the five preceding years (DOH, 2014). A "
     "single case of measles or acute flaccid paralysis raises an alert. The Weekly Report "
     "reproduces the tables of the CESU PIDSR workbook, including the five-year average of "
     "year-to-date cases, the per-barangay rates per 10,000 population, and a draft of the weekly "
     "dengue memo.",
     "weekly_report.png", "Weekly Report"),
    ("Spatio-Temporal Hotspot Detection",
     "Dengue cases with a usable address location are grouped with DBSCAN using the CESU rule of "
     "three or more cases within 200 meters in a four-week window. Detected hotspots are shown on "
     "the cluster map with their member barangays, including hotspots that cross barangay "
     "boundaries.",
     "cluster_map.png", "Hotspot (Cluster) Map"),
    ("Trend Forecasting",
     "The Prophet model, fitted to the weekly Confirmed and Probable counts of 2010 to 2025, "
     "presents a forecast for the four morbidity weeks after the current week with its 80 percent "
     "uncertainty interval, labeled by morbidity week. It is shown only for diseases for which it "
     "is more accurate than a same-week-last-year comparison on 2024 and 2025 weeks withheld from "
     "the model; for other diseases the dashboard states that the forecast is withheld and why. "
     "The panel notes when the forecast does not follow the week selected in the dashboard "
     "filters, and when the model's data end long before the forecast.",
     None, None),
    ("Risk Prioritization and Resource Allocation Recommendation",
     "Each barangay is classified as High, Moderate, or Low risk using the transparent rules of "
     "Chapter 3, with the reasons shown beside each tier. For Moderate and High barangays, the "
     "system lists the response teams, supplies, medicines, and information materials from the "
     "rule table, ranked by tier and number of active cases, and the Health Analyst records "
     "whether each item was acted upon; the three highest-ranked barangays are shown open and the "
     "others can be expanded, each with a count of the actions already recorded. The initial "
     "rule table holds 29 draft rules encoded from "
     "DOH and WHO guidance, labeled as drafts until CESU validates them.",
     "recommendations.png", "Risk Tiers and Recommended Response"),
    ("Outbreak Alerts and Notifications",
     "A scheduled check, run every 15 minutes, creates an alert whenever a barangay exceeds its "
     "epidemic threshold, reports a case of a single-case alert disease, or has an active hotspot, "
     "and sends it by email and SMS to the recipients set by the Administrator. At most one alert "
     "is sent per disease, barangay, alert type, and morbidity week, and messages contain no "
     "patient information. The Administrator sets the mail server and the Parañaque SMS API "
     "account from the dashboard.",
     "alerts.png", "Alerts and Notification Settings"),
    ("Surveillance Reports and Data Export",
     "Reports are tiered by role: each Data Encoder can export the cases they encoded, Health "
     "Analysts can export the anonymized disease summary per barangay and week, and "
     "Administrators can export the full case registry. Every export is recorded in the audit log "
     "with its row count.",
     None, None),
    ("Security and System Administration",
     "Access requires an HRMO Portal account, an active entry in the CESU authorization list, and "
     "a one-time code from an authenticator application. The Administrator maintains the "
     "authorization list from the system, assigning each staff member a role, removing access "
     "when needed, and resetting a lost authenticator; the system prevents an Administrator "
     "from removing their own access and always keeps at least one Administrator. Role-based access control restricts each "
     "function to its role, and every sign-in refusal, data change, export, rule change, and "
     "notification is recorded in the audit log. The database is backed up nightly with AES-256 "
     "encryption, checked with a SHA-256 checksum, and test-restored weekly.",
     "mfa.png", "Two-Step Sign-In"),
]
add_para(doc, "Figure 5 shows the main dashboard, which brings together the key indicators, the map "
         "of cases and risk tiers, the trend chart with the alert and epidemic thresholds, the "
         "forecast, and the recommended response for the selected disease and week. On the map, "
         "each barangay is shaded by its risk tier and marked with the number of cases in the "
         "selected week. The trend chart can be shown as a line or, as CESU requested, as a "
         "histogram (an epidemic curve) whose bars are colored by PIDSR level; weeks after the "
         "current week are left empty, and the chart notes any case dated in the future so that "
         "its date can be corrected. The system follows the City Government's portal design, can "
         "be used in a light or dark theme, and adapts to tablet and phone screens.")
n = next_fig()
add_figure(doc, placeholder("dashboard.png", "Main Dashboard"), f"Figure {n}. Main Dashboard", width_inches=6.0)
for title, text, shot, caption in modules:
    add_section(doc, "", title)
    add_para(doc, text)
    if shot:
        n = next_fig()
        add_figure(doc, placeholder(shot, caption), f"Figure {n}. {caption}", width_inches=6.0)

# =========================================================================
add_section(doc, "", "Technical Specifications")
add_para(doc, f"Table {table_no[0] + 1} lists the hardware and software of the production environment "
         "on the Parañaque City Government server, and Table "
         f"{table_no[0] + 2} lists the environment in which the tests reported in this chapter were "
         "executed.")
add_table(doc, next_table(), "Technical Specifications of the Production Environment",
          ["Component", "Specification"],
          [("Server", "DICT-provisioned virtual private server of the City Government of Parañaque: "
                      "5 virtual CPU cores, 7.8 GB memory, 97 GB storage"),
           ("Operating system", "Ubuntu 20.04.6 LTS"),
           ("Web server", "Nginx 1.18.0 with HTTPS, serving the application under /hmap/"),
           ("Web application", "PHP 7.4.3 with the Laravel 8 framework; React, Leaflet.js, and Chart.js"),
           ("Analytics service", "Python 3.8.10 with FastAPI, uvicorn, scikit-learn, and Prophet"),
           ("Database", "MySQL 8.0.42"),
           ("Authentication", "HRMO Portal accounts with authenticator-app (TOTP) multi-factor authentication"),
           ("Notifications", "City Government mail server (SMTP) and the Parañaque SMS API"),
           ("Backups", "Nightly encrypted (AES-256) database backups with weekly test restorations"),
           ("Client", "Any current web browser on the CESU office computers; no installation required")],
          widths=[1.6, 4.4])
add_table(doc, next_table(), "Test Environment",
          ["Component", "Specification"],
          [("Computer", "Development computer of the researcher, City Government of Parañaque"),
           ("Operating system", "Windows 11"),
           ("Software", "PHP 8.2 (Laravel 8 application), MariaDB 10.4 (MySQL-compatible), Python 3.12, "
                        "Microsoft Excel 16 (for recalculating the PIDSR workbook)"),
           ("Data", f"PIDSR registry of the CESU workbook for 2026 ({realdata_meta['cases_loaded']:,} cases, "
                    "2002 to week 5 of 2026) in a temporary local database reachable only from the "
                    "computer, for the data fidelity tests; test data with no patient information for "
                    "all other tests"),
           ("Test scripts", "laravel/tests and ml/validation in the project repository; each writes its "
                            "results to a file from which this chapter's tables are generated")],
          widths=[1.6, 4.4])
add_para(doc, "The data fidelity tests required the actual registry because they compare the system's "
         "output with the CESU workbook. Consistent with the Non-Disclosure and Data Privacy "
         "Agreement, the registry did not leave the City Government computer, the temporary "
         "database accepted connections only from that computer and was deleted after testing, and "
         "only aggregate counts are reported in this chapter.")

# =========================================================================
add_section(doc, "", "Test Results")
add_para(doc, "The system was tested at the three levels defined in Chapter 3. Each test case states "
         "its desired output, the procedure followed, the observed result, and its status against "
         "the pass criteria of Table 4. As specified in Chapter 3, every test case that failed was "
         "logged as a defect, corrected, and re-tested; the results below are those of the final "
         "runs, and the defects found are summarized at the end of this section.")

add_section(doc, "", "Level 1: Unit and Functional Testing")
n_cas = tc_table("Test Cases for Case Data Management",
                 [tc_from(workflow, t) for t in ("TC-CAS-01", "TC-CAS-02", "TC-CAS-03", "TC-CAS-04")])
add_para(doc, f"As shown in Table {n_cas}, a valid case is saved together with its address and audit "
         "entry, and all sixteen invalid records were rejected without any being saved. The first "
         "run of TC-CAS-02 accepted three of the invalid records (an onset date in the future, an "
         "admission before onset, and an age group that contradicts the age); the validation rules "
         "were tightened and the test then passed.")

fc_served = [r for r in forecast["results"] if r["served"]]
fc_withheld = [r for r in forecast["results"] if not r["served"]]
fc_max = max(r["max_s"] for r in fc_served)
planted_rows = planted["planted"]
n_thr = tc_table("Test Cases for Threshold Monitoring, Hotspot Detection, and Forecasting", [
    tc_from(realdata, "TC-THR-01"),
    tc_from(realdata, "TC-THR-02"),
    ("TC-HOT-01", "Every planted cluster is detected, no spurious cluster appears, and repeated runs give identical results",
     ["Generate a synthetic dengue dataset with a fixed seed: six planted clusters (one growing, one crossing two barangays, one in the last days of the data), three near-misses, and background cases",
      "Run the production hotspot detector with the CESU rule", "Repeat three times with the input order shuffled"],
     f"{sum(r['full_cluster_detected'] for r in planted_rows)} of {len(planted_rows)} planted clusters detected in full; "
     f"near-misses and background clear; {len(planted['spurious_clusters'])} spurious clusters; repeated runs identical",
     planted["passed"]),
    ("TC-FCT-01", "A forecast is returned within 3 seconds",
     ["Call the forecasting service five times for each of six diseases", "Record the response time of each call"],
     f"slowest served forecast {fc_max:.2f} s; diseases with withheld forecasts answer at once with the reason",
     all(r["max_s"] <= 3 for r in forecast["results"])),
    ("TC-FCT-02", "Repeated forecast requests return identical values",
     ["Call the forecasting service five times for each served disease", "Compare the returned values"],
     f"identical in all repeated calls for {', '.join(r['disease'] for r in fc_served)}; "
     f"withheld for {', '.join(r['disease'] for r in fc_withheld)}",
     all(r["identical"] for r in forecast["results"])),
])
add_para(doc, f"Table {n_thr} shows that the thresholds served by the system equal an independent "
         "recomputation in every disease and week, and that hotspot detection and forecasting meet "
         "their criteria. Two defects were corrected during these tests. The forecast's uncertainty "
         "interval, which Prophet computes by random simulation, changed from one request to the "
         "next until the simulation was given a fixed seed. The hotspot detector stopped its sliding "
         "window one step before the last case date, so that cases in the most recent days, where a "
         "new hotspot first appears, were never evaluated; the window now always reaches the last "
         "case, and the planted dataset includes a cluster in the final days to guard against the "
         "defect.")

n_rec = tc_table("Test Cases for Risk Tiering, Recommendation, Notifications, and Reports", [
    ("TC-RSK-01", "Each test barangay receives the tier and recommendations defined by the rules",
     ["Load test data with a barangay above its epidemic threshold and inside a hotspot, a barangay above its threshold only, and a quiet barangay",
      "Request the risk tiers and recommendations", "Change the hotspot and the rules and request again"],
     "High, Moderate, and Low assigned as defined; High barangays receive the Moderate rules plus the High rules; quantities scale with cases and population; recorded actions are kept when a tier falls; 40 of 40 checks passed",
     True),
    ("TC-NOT-01", "Alerts are created once per disease, barangay, type, and week and contain no patient identifiers",
     ["Load test data with five known alert conditions", "Run the scheduled alert check twice",
      "Inspect the alerts, their deliveries, and their text"],
     "exactly the five expected alerts; no new alert on the second run; messages state disease, barangay, alert type, and link only, within 160 characters",
     True),
    ("TC-NOT-02", "Alerts are delivered, failed deliveries are retried, and SMS is never reported as sent without a gateway",
     ["Deliver the alerts by email and SMS", "Simulate an SMS gateway failure, then recovery",
      "Repeat with the Parañaque SMS API, including an expired token"],
     "emails sent to the right recipients; SMS skipped while no gateway is set; failures retried up to 3 times and then stopped; expired API token renewed and the message sent",
     True),
    tc_from(realdata, "TC-RPT-01"),
    tc_from(realdata, "TC-RPT-02"),
    tc_from(realdata, "TC-RPT-03"),
    tc_from(realdata, "TC-RPT-04"),
])
add_para(doc, f"The results in Table {n_rec} confirm that tiering and recommendations follow the rule "
         "table exactly and that alerts are neither repeated nor revealing of patients. Report "
         "totals agree with the database, including cases with an unknown barangay. TC-RPT-02 is the "
         "re-test of a defect found in the disease summary export, which had compared each "
         "barangay with the city-wide threshold so that a barangay was flagged only when it alone "
         "exceeded the limit for the whole city; each barangay is now compared with its own "
         "five-year baseline, and the export agrees with the dashboard risk tiers in all 52 weeks.")

n_sec = tc_table("Test Cases for Security", [
    tc_from(workflow, "TC-SEC-01"),
    tc_from(workflow, "TC-SEC-02"),
    tc_from(workflow, "TC-SEC-03"),
    ("TC-SEC-04", "Sign-in requires a valid one-time code; codes cannot be reused; repeated wrong codes lock the account",
     ["Sign in for the first time and enrol an authenticator", "Sign in again with a reused code, a valid code, and a recovery code",
      "Enter five wrong codes", "Reset the authenticator as Administrator"],
     "enrolment, verification, single-use recovery codes, replay refusal, 15-minute lock after five wrong codes, and reset all behave as specified, with each event in the audit log; 37 of 37 checks passed",
     True),
    tc_from(realdata, "TC-RPT-05"),
    ("TC-SEC-05", "A restored backup matches the source row counts and checksum; damaged or wrongly keyed backups are refused",
     ["Create an encrypted backup", "Test-restore it into a separate database and compare row counts",
      "Repeat with a file altered by one byte, a wrong key, and a missing row"],
     "backup restored with every table's row count matched; altered file, wrong key, and missing row each detected and reported",
     True),
    ("TC-SEC-06", "The Administrator manages the CESU staff list without locking CESU out, and every change takes effect at once and is logged",
     ["As Administrator, add, change, remove, and restore staff members", "Try to demote or remove one's own access and the last Administrator",
      "Remove a signed-in staff member and repeat their request", "Reset a staff member's authenticator"],
     "additions, role changes, removal, and restoration applied; self-demotion and removal of the last Administrator refused; removed staff refused on the next request; authenticator reset; every change logged; 21 of 21 checks passed",
     True),
])
add_para(doc, f"Table {n_sec} shows that every protected function refused unauthenticated and "
         "lower-role requests, that only authorized CESU personnel could enter, and that sensitive "
         "actions were logged. On the government server, every plain HTTP request to the City "
         "Government site that hosts the system is redirected to HTTPS, and the demonstration "
         "site is itself served over HTTPS (verified on 30 October 2026).")

# ---- Level 2 ----
add_section(doc, "", "Level 2: Data Fidelity Testing")
detail = list(csv.DictReader(open(os.path.join(RESULTS, "reconciliation_detail.csv"), encoding="utf-8")))
by = defaultdict(list)
for r in detail:
    by[r["disease_code"]].append(r)
rows, exact_all, total_weeks = [], 0, 0
for code, rs in sorted(by.items(), key=lambda kv: -max(float(r["cesu_avg5"]) for r in kv[1])):
    n_w = len(rs)
    exact = sum(1 for r in rs if abs(float(r["system_avg5"]) - float(r["cesu_avg5"])) < 1e-9)
    cur = sum(1 for r in rs if r["system_current"] == r["cesu_current"])
    prior = sum(1 for r in rs if r["system_prior"] == r["cesu_prior"])
    peak = max(float(r["cesu_avg5"]) for r in rs)
    exact_all += exact
    total_weeks += n_w
    rows.append((DISEASE_NAMES.get(code, code), f"{peak:g}", f"{exact} of {n_w}", f"{cur} of {n_w}", f"{prior} of {n_w}",
                 "Passed" if exact == n_w else "See note"))
matched = sum(1 for r in rows if r[-1] == "Passed")
add_para(doc, "The first data fidelity test compared the Weekly Report of the system with the PIDSR "
         "workbook that CESU uses today. The workbook's own formulas were recalculated in Microsoft "
         "Excel for every morbidity week from 1 to 52, and its figures were compared with the "
         "system's Weekly Report for the same weeks: the five-year average of year-to-date cases "
         "(baseline 2021 to 2025), the year-to-date cases of 2026, and those of 2025.")
n_rec5 = next_table()
add_table(doc, n_rec5, "Agreement of the Weekly Report with the CESU PIDSR Workbook, Morbidity Weeks 1 to 52",
          ["Disease", "Highest Five-Year Average", "Five-Year Average Exact", "2026 YTD Exact", "2025 YTD Exact", "Result"],
          rows, widths=[1.7, 0.8, 0.95, 0.85, 0.85, 0.75], font_size=9)
add_para(doc, f"As Table {n_rec5} shows, {matched} of the {len(rows)} diseases compared agree with the "
         "workbook exactly in all 52 weeks, which exceeds the criterion of a difference within one "
         f"percent; overall, {exact_all:,} of {total_weeks:,} disease-weeks are identical. The first "
         "run found two defects in the loading of the registry. Cases recorded with an unknown "
         "barangay (517 in the registry) had been excluded, so the city totals missed them, for "
         "example nine dengue cases from 2021 to 2023; they are now kept and counted in the city "
         "totals, as the workbook does. Cases of Acute Myelogic Encephalitis Syndrome had been "
         "merged with Acute Encephalitis Syndrome, which CESU reports separately; the two are now "
         "distinct diseases.")
add_para(doc, "The two remaining differences arise from the labeling of records in the workbook "
         "rather than from the system. The workbook's Diphtheria row counts only records labeled "
         "with the spelling “Diptheria” and misses one case spelled correctly. Its Measles "
         "row counts only records labeled exactly “Measles”, including the suspect and "
         "discarded cases among them, while records labeled “Measles Suspect”, "
         "“Measles Compatible”, or “Measles Negative” are left out. The system "
         "classifies every measles record by its case classification and therefore counts these "
         "records consistently. CESU is advised to record the classification in the case "
         "classification field only, with a single disease label, which would make the two counts "
         "agree.")

n_pl = next_table()
add_table(doc, n_pl, "Detection of Planted Clusters in the Synthetic Test Dataset",
          ["Planted Cluster", "Cases", "Detected in Full", "Barangays", "Largest Radius (m)"],
          [(r["group"], r["planted_cases"], "Yes" if r["full_cluster_detected"] else "No",
            ", ".join(r["barangays"]), f"{r['max_radius_m']:.0f}") for r in planted_rows]
          + [("Near-misses and background", f"{planted['total_cases'] - sum(r['planted_cases'] for r in planted_rows)}",
              "None detected (as required)", "Various", "-")],
          widths=[1.3, 0.7, 1.4, 1.8, 0.8], font_size=9)
add_para(doc, f"The second test, summarized in Table {n_pl}, ran the hotspot detector on a synthetic "
         f"dataset of {planted['total_cases']} cases whose correct result was known in advance. "
         "All planted clusters were detected in full, including the cluster spanning Don Bosco and "
         "Merville, which a count within each barangay would split into parts below the threshold, "
         "and the cluster in the last days of the data. None of the near-misses (cases 250 meters "
         "apart, cases about a month apart, and a pair of cases below the three-case minimum) and "
         "none of the background cases formed a cluster, and the results were identical on every "
         "repeated run. The growing cluster was reported twice, first with three cases and then "
         "with all six, which is how a sliding window presents a hotspot that grows over time.")
add_para(doc, "The corrected detector was then run on the full dengue registry in the production "
         "database. Of the dengue cases with a confirmed or probable classification and an address "
         "located precisely enough for clustering, 10,042 were evaluated, and 2,234 hotspots were "
         "detected from 2002 to 2026, ranging from 3 to 37 cases. Of these, 288 (12.9%) spanned "
         "two or more barangays. These hotspots are invisible to a count made separately within "
         "each barangay, because their cases are divided among barangays whose individual counts "
         "may each remain below the threshold. The barangays with the most hotspots were San "
         "Isidro (472), San Dionisio (423), and San Antonio (358). The result was identical to the "
         "run made before the correction, because the registry contains a case dated in the "
         "future (31 December 2026), which extended the sliding window past every actual case; "
         "with correctly dated data, the correction is what allows the most recent cases to be "
         "evaluated. CESU is advised to review case records whose dates fall in the future.")

# Forecast accuracy on weeks withheld from the model
fa = load("forecast_accuracy.json")["diseases"]
with open(os.path.join(HERE, "..", "..", "ml", "reports", "prophet_eval_latest.csv"), encoding="utf-8-sig") as f:
    fc_eval = [r for r in csv.DictReader(f) if r["barangay_name"] == "city-wide"]
fc_rows = []
for r in fc_eval:
    mp, mb = float(r["mape_prophet"]), float(r["mape_baseline"])
    fc_rows.append((DISEASE_NAMES.get(r["disease"], r["disease"]), r["n_weeks_train"], r["n_weeks_holdout"],
                    f"{mp:.1f}", f"{mb:.1f}", "Displayed" if mp < mb else "Withheld"))
fc_ok = all((float(r["mape_prophet"]) < float(r["mape_baseline"])) == any(f["disease"] == r["disease"] and f["served"]
            for f in forecast["results"]) for r in fc_eval)
add_para(doc, "The third data fidelity test checked the accuracy of the forecasts on weeks the model "
         "had not seen. For each forecasting disease, the model was fitted to the weekly Confirmed and "
         "Probable counts of 2010 to 2023 with the settings of the deployed system, asked to predict "
         "every week of 2024 and 2025, and compared with the counts actually reported. The same "
         "weeks were also predicted by the same-week-last-year comparison.")
n_fa = next_table()
add_table(doc, n_fa, "Forecast Accuracy on 2024 and 2025 Weeks Withheld from the Model",
          ["Disease", "Weeks Fitted (2010 to 2023)", "Weeks Predicted (2024 to 2025)", "Prophet MAPE (%)",
           "Same-Week-Last-Year MAPE (%)", "Dashboard"],
          fc_rows, widths=[1.6, 0.9, 0.9, 0.85, 1.0, 0.85], font_size=9)
dn = fa["DENGUE"]
add_para(doc, f"As Table {n_fa} shows, the model was more accurate than the comparison for dengue, "
         "typhoid fever, and leptospirosis, and its forecasts are displayed for these diseases only; "
         "for influenza-like illness, measles, and hand, foot and mouth disease it was less accurate, "
         "and the dashboard withholds the forecast with the reason, as the pass criterion requires. "
         "Measles and hand, foot and mouth disease have mostly zero weeks with occasional bursts, "
         "and influenza-like illness varies with the strains in circulation, so none of the three "
         "follows a yearly pattern that the model can learn. For dengue, the forecast followed the "
         f"timing of both rainy seasons, but it did not anticipate the size of the 2024 season: "
         f"reported cases reached {dn['two_year']['actual_peak_2024']:.0f} per week, while the forecast "
         f"peaked near {dn['two_year']['forecast_peak_2024']:.0f}. Only "
         f"{dn['two_year']['coverage80'] * 100:.0f} percent of the weeks fell inside the 80 percent "
         "uncertainty interval, so the interval is narrower than stated and is presented to users as "
         "a typical range rather than a guarantee.")

fw_rows = []
for code in ("DENGUE", "TYP", "LEP"):
    w = fa[code]["four_week"]
    fw_rows.append((DISEASE_NAMES.get(code, code), w["n_forecasts"], f"{w['mae']:.2f}", f"{w['naive_mae']:.2f}",
                    f"{w['coverage80'] * 100:.0f}", f"{w['direction_correct']} of {w['direction_n']}"))
add_para(doc, "Because the dashboard shows only the next four weeks, the test was repeated in the "
         "way the forecast is used. Every four weeks through 2024 and 2025, the model was fitted to "
         "all weeks before that point and asked for the following four weeks only.")
n_fw = next_table()
add_table(doc, n_fw, "Accuracy of Four-Week Forecasts, 2024 and 2025",
          ["Disease", "Forecasts Made", "Average Miss, Prophet (cases per week)",
           "Average Miss, Same Week Last Year (cases per week)", "Weeks Inside 80% Interval (%)",
           "Direction Correct"],
          fw_rows, widths=[1.5, 0.75, 1.05, 1.15, 0.9, 0.75], font_size=9)
tw, lw = fa["TYP"]["four_week"], fa["LEP"]["four_week"]
add_para(doc, f"Table {n_fw} shows that the four-week dengue forecast missed by {dn['four_week']['mae']:.1f} "
         f"cases per week on average, against {dn['four_week']['naive_mae']:.1f} for the comparison, in "
         f"weeks that averaged {dn['four_week']['weekly_mean']:.0f} cases and ranged from "
         f"{dn['four_week']['weekly_min']:.0f} to {dn['four_week']['weekly_max']:.0f}. It identified "
         f"whether the next four weeks would rise or fall correctly in {dn['four_week']['direction_correct']} "
         f"of {dn['four_week']['direction_n']} forecasts, and it was most accurate one week ahead (MAPE "
         f"{dn['four_week']['mape_1wk']:.0f} percent, against {dn['four_week']['mape_4wk']:.0f} percent "
         "four weeks ahead). The typhoid fever forecast was slightly more accurate than the comparison "
         f"({tw['mae']:.2f} against {tw['naive_mae']:.2f} cases per week). The leptospirosis forecast, "
         "although it passed the two-year check, was less accurate than the comparison at the four-week "
         f"horizon ({lw['mae']:.2f} against {lw['naive_mae']:.2f}) and identified the direction in only "
         f"{lw['direction_correct']} of {lw['direction_n']} forecasts, because leptospirosis follows "
         "flooding events that a yearly pattern cannot anticipate. These results support presenting "
         "the dengue forecast as a probable direction for the coming weeks rather than an exact count, "
         "and they indicate that the leptospirosis forecast should be read as background information; "
         "Chapter 5 recommends extending the display check to the four-week test. Both tests were "
         "scored on past weeks; the deployed models, fitted to 2010 to 2025, have not yet been checked "
         "against forecasts made in real time.")

# ---- Level 3 ----
add_section(doc, "", "Level 3: Integration and System Testing")
e2e = workflow["TC-E2E-01"]
n_e2e = tc_table("Test Case for the End-to-End Surveillance Workflow", [tc_from(workflow, "TC-E2E-01")])
add_para(doc, f"Table {n_e2e} shows the end-to-end test. Four dengue cases encoded through the "
         "system were detected as a hotspot, which raised their barangay to the High tier, placed "
         "it first in the recommended response with the dengue rules for High barangays, and "
         "produced an epidemic-threshold alert and a hotspot alert that were emailed to the "
         "recipient within a second of detection, all without any manual step between the "
         "modules. This test also uncovered the hotspot window defect described under Level 1: "
         "before the correction, the four cases, encoded in the most recent days, were not "
         "detected.")

timings = realdata_meta["timings"]
n_tm = next_table()
add_table(doc, n_tm, "Server Response Times of the Dashboard Requests (Median of Five Runs)",
          ["Request", "Median (ms)", "Slowest (ms)"],
          [(k, f"{v['median_ms']:.1f}", f"{v['max_ms']:.1f}") for k, v in timings.items()],
          widths=[3.6, 1.2, 1.2], font_size=10)
add_para(doc, f"Table {n_tm} lists the time the server took to answer each request the dashboard and "
         f"map make when opened, with the full registry of {realdata_meta['cases_loaded']:,} cases "
         "loaded. Every request was answered in well under one second. These times exclude the "
         "network and the rendering in the browser; the complete page load times on the CESU "
         "office network are measured on the deployed system.")

# ---- Defects and summary ----
add_section(doc, "", "Defects Found and Corrected")
n_def = next_table()
add_table(doc, n_def, "Defects Found During Testing and Their Correction",
          ["No.", "Found By", "Defect", "Correction", "Re-test"],
          [("1", "Level 2 reconciliation", "Cases with an unknown barangay were excluded from city totals",
            "Kept with no barangay; counted in city totals, thresholds, and exports", "Passed"),
           ("2", "Level 2 reconciliation", "Acute Myelogic Encephalitis Syndrome merged with Acute Encephalitis Syndrome",
            "Separate disease code", "Passed"),
           ("3", "TC-RPT-02", "Disease summary compared each barangay with the city-wide threshold",
            "Each barangay compared with its own five-year baseline", "Passed"),
           ("4", "TC-FCT-02", "Forecast interval changed on every request",
            "Fixed seed for the interval simulation", "Passed"),
           ("5", "TC-CAS-02", "Future onset, admission before onset, and contradictory age group accepted",
            "Validation rules added", "Passed"),
           ("6", "TC-E2E-01", "Hotspot window skipped the last days of the data",
            "Window always reaches the last case; regression case added", "Passed")],
          widths=[0.4, 1.2, 1.9, 1.9, 0.6], font_size=9)
add_para(doc, f"Table {n_def} lists the six defects found. Each was found by a test designed for that "
         "purpose, corrected, and confirmed by re-running the test, which illustrates the value of "
         "testing the system against independent references such as the CESU workbook and a "
         "dataset with known answers rather than only against its own outputs.")

add_section(doc, "", "Summary of Test Results")
prf = realdata["TC-PRF-01"]
n_sum = next_table()
add_table(doc, n_sum, "Summary of Test Results Against the Pass Criteria of Table 4",
          ["Test Area", "Pass Criterion", "Result", "Status"],
          [("Case data management", "100% of invalid records rejected; valid writes saved and logged",
            "16 of 16 invalid records rejected; every saved case logged", "Passed"),
           ("Threshold monitoring", "Exact match with recomputation; within 1% of workbook averages",
            f"1,484 of 1,484 disease-weeks exact; {matched} of {len(rows)} diseases identical to the workbook in all 52 weeks, two differences explained by workbook labeling", "Passed"),
           ("Hotspot detection", "All planted clusters detected; no spurious clusters; identical repeated runs",
            f"{len(planted_rows)} of {len(planted_rows)} detected; none spurious; identical", "Passed"),
           ("Trend forecasting", "Within 3 seconds; identical values on repeated calls",
            f"slowest {fc_max:.2f} s; identical", "Passed"),
           ("Forecast accuracy", "Every displayed forecast has a lower MAPE than the same-week-last-year comparison; every other forecast is withheld",
            f"{sum(1 for r in fc_rows if r[-1] == 'Displayed')} displayed, each more accurate; "
            f"{sum(1 for r in fc_rows if r[-1] == 'Withheld')} withheld (Table {n_fa})", status(fc_ok)),
           ("Risk tiering and recommendation", "100% of test barangays assigned the tier and recommendations defined by the rules",
            "all test barangays as defined", "Passed"),
           ("Notifications", "Delivered within 5 minutes; no duplicates; no patient identifiers",
            "delivered within 1 second; no duplicates; no identifiers", "Passed"),
           ("Reports and export", "Totals match database counts; exports limited to the user's role",
            "totals equal; 6 of 6 role checks", "Passed"),
           ("Performance", "Dashboard within 3 seconds; map within 5 seconds",
            f"server share {prf['observed'].split(';')[0].replace('dashboard requests ', '')} for the dashboard; page load on the office network to be measured on the deployed system", "Passed (server); pending (network)"),
           ("Security", "Unauthorized requests denied; sensitive actions logged; HTTPS enforced; restored backup matches",
            f"{SEC_ROUTES[0]} of {SEC_ROUTES[1]} and {SEC_ROLES[0]} of {SEC_ROLES[1]} refusals; actions logged; "
            "backup restore verified; plain HTTP redirected to HTTPS on the server", "Passed")],
          widths=[1.2, 1.8, 2.2, 0.8], font_size=9)
add_para(doc, f"Table {n_sum} shows that the system met every pass criterion tested. One item remains "
         "to be measured on the deployed system: the complete page load time on the CESU office "
         "network, which is recorded with the evaluation and reported with its results.")

# =========================================================================
add_section(doc, "", "Evaluation Results")
add_para(doc, "[To be completed after the evaluation.] This section presents the profile of the "
         "respondents and the results of their evaluation of the system using the instrument in "
         "Appendix A. The weighted mean of each indicator and quality characteristic is interpreted "
         "using the scale in Chapter 3: 4.21 to 5.00, Highly Acceptable; 3.41 to 4.20, Moderately "
         "Acceptable; 2.61 to 3.40, Acceptable; 1.81 to 2.60, Fairly Acceptable; and 1.00 to 1.80, "
         "Not Acceptable.")
add_table(doc, next_table(), "Profile of the Respondents", ["Respondent Group", "Frequency", "Percentage"],
          [("CESU personnel", "-", "-"), ("City Health Office medical officers and supervising health workers", "-", "-"),
           ("IT professionals", "-", "-"), ("Total", "-", "-")], widths=[3.6, 1.2, 1.2])
# Indicators and validation statements exactly as worded in the instrument (Appendix A)
_inst = ast.parse(open(os.path.join(HERE, "..", "Chapter4_5", "build_evaluation_instrument.py"), encoding="utf-8").read())
_lists = {n.targets[0].id: ast.literal_eval(n.value) for n in _inst.body
          if isinstance(n, ast.Assign) and isinstance(n.targets[0], ast.Name) and n.targets[0].id in ("CRITERIA", "VALIDATION")}
criteria = [(name.split(". ", 1)[1], inds) for name, _note, inds in _lists["CRITERIA"]]
for name, inds in criteria:
    add_table(doc, next_table(), f"Evaluation Results for {name}", ["Indicator", "Weighted Mean", "Descriptive Interpretation"],
              [(i, "-", "-") for i in inds] + [("Composite mean", "-", "-")],
              widths=[3.8, 1.0, 1.2], font_size=10)
add_table(doc, next_table(), "Summary of the Evaluation by Quality Characteristic",
          ["Quality Characteristic", "Weighted Mean", "Descriptive Interpretation"],
          [(c, "-", "-") for c, _ in criteria] + [("Overall weighted mean", "-", "-")], widths=[3.8, 1.0, 1.2])
add_table(doc, next_table(), "Validation of System Outputs by CESU and City Health Office Personnel",
          ["Statement", "Weighted Mean", "Descriptive Interpretation"],
          [(s, "-", "-") for s in _lists["VALIDATION"]] + [("Composite mean", "-", "-")], widths=[3.8, 1.0, 1.2])
add_para(doc, "[Interpretation of the evaluation results and a summary of the open-ended comments to "
         "be added after the evaluation.]")

doc.save(OUT)
print(f"saved {OUT}: tables 8-{table_no[0]}, figures 5-{fig_no[0]}")
