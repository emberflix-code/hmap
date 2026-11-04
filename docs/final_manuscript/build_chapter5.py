"""Build Chapter5_Summary_Conclusions.docx (TUP outline: Summary of Findings,
Conclusions, Recommendations).

Formatting helpers come from build_chapters_final.py, as in build_chapter4.py.
Findings are organized by the specific objectives of Chapter 1, and figures
are read from the same result files as Chapter 4 (docs/Chapter4_5/results/),
so the two chapters always agree. Findings and conclusions on the evaluation
(Specific Objective 4) are placeholders until the evaluation is conducted.

Usage: python build_chapter5.py
"""
import csv
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.join(HERE, "..", "Chapter4_5", "results")
OUT = os.path.join(HERE, "Chapter5_Summary_Conclusions.docx")

_src = open(os.path.join(HERE, "build_chapters_final.py"), encoding="utf-8").read()
exec(compile(_src.split("# Build document")[0], "build_chapters_final.py (helpers)", "exec"))


def load(name):
    with open(os.path.join(RESULTS, name), encoding="utf-8") as f:
        return json.load(f)


real = load("realdata_tests.json")
_wf = {t["id"]: t["observed"] for t in load("workflow_tests.json")["tests"]}
SEC_ROUTES = re.search(r"of (\d+) routes", _wf["TC-SEC-01"]).group(1)
SEC_ROLES = re.search(r"of (\d+) lower-role", _wf["TC-SEC-02"]).group(1)
planted = load("planted_clusters_result.json")
forecast = load("forecast_timing.json")
detail = list(csv.DictReader(open(os.path.join(RESULTS, "reconciliation_detail.csv"), encoding="utf-8")))
codes = sorted({r["disease_code"] for r in detail})
identical = [c for c in codes if all(abs(float(r["system_avg5"]) - float(r["cesu_avg5"])) < 1e-9
                                     for r in detail if r["disease_code"] == c)]
served = [r["disease"] for r in forecast["results"] if r["served"]]
withheld = [r["disease"] for r in forecast["results"] if not r["served"]]
fc_max = max(r["max_s"] for r in forecast["results"] if r["served"])
fa = load("forecast_accuracy.json")["diseases"]
dw, lw = fa["DENGUE"]["four_week"], fa["LEP"]["four_week"]
cases = real["cases_loaded"]

doc = Document()
doc.core_properties.author = "Kemberly M. Magsino"
doc.core_properties.title = ("Web-Based Disease Outbreak Management System for the City "
                             "Epidemiology and Surveillance Unit: Chapter 5")
doc.styles["Normal"].font.name = "Times New Roman"
doc.styles["Normal"].font.size = Pt(12)
sec = doc.sections[0]
sec.page_width, sec.page_height = Inches(8.5), Inches(11)
sec.top_margin = sec.bottom_margin = sec.right_margin = Inches(1)
sec.left_margin = Inches(1.5)
hp = sec.header.paragraphs[0]
hp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
add_page_number_field(hp)

add_chapter_break(doc, "Chapter 5", "SUMMARY OF FINDINGS, CONCLUSIONS, AND RECOMMENDATIONS", page_break=False)
add_para(doc, "This chapter summarizes the findings of the study, presents the conclusions drawn "
         "from them in relation to the objectives stated in Chapter 1, and offers recommendations "
         "to the City Epidemiology and Surveillance Unit, the City Health Office, the City "
         "Government of Parañaque, and future researchers.")

# =========================================================================
add_section(doc, "", "Summary of Findings")
add_para(doc, "The study developed a Web-Based Disease Outbreak Management System for the City "
         "Epidemiology and Surveillance Unit (CESU) of Parañaque City that detects, locates, "
         "prioritizes, recommends, and notifies. The findings are presented according to the "
         "specific objectives of the study.")

add_numbered(doc, 1, "Design of the system. The system was designed with the nine modules "
             "specified in the objectives: case data management; disease mapping across the 16 "
             "barangays; epidemic threshold monitoring based on the PIDSR alert and epidemic "
             "thresholds, the single-case triggers, and the CESU five-year average; "
             "spatio-temporal hotspot detection with the CESU rule of three or more cases within "
             "200 meters and four weeks; trend forecasting with the Prophet model; rule-based risk "
             "prioritization and resource allocation recommendation; SMS and email "
             "notifications; surveillance reports and data export; and security and system "
             "administration. The recommendation rule table was initialized with 29 draft rules "
             "encoded from DOH and WHO guidance, to be validated by CESU.")
add_numbered(doc, 2, "Development of the system. The system was developed with PHP 7.4 and the "
             "Laravel 8 framework, MySQL 8, React, Leaflet.js with OpenStreetMap, Chart.js, and a "
             "Python 3.8 FastAPI analytics service applying DBSCAN and Prophet, for deployment "
             "on the DICT-provisioned server of the City Government. Access is limited to CESU "
             "personnel on the authorization list, who sign in with their HRMO Portal account and "
             "a one-time code from an authenticator application. The Administrator maintains the "
             "authorization list, the recommendation rules, the notification recipients, and the "
             "email and SMS settings, including the Parañaque SMS API, from the system itself.")
add_numbered(doc, 3, "Testing of the system. The system passed every test that can be performed "
             "before deployment, at all three levels of testing:")
add_sublettered(doc, "a", "Case encoding, import, validation, and audit logging: all 16 invalid "
                "test records were rejected, valid records were saved with their audit entries, "
                "and CSV uploads saved valid rows while reporting each rejected row.")
add_sublettered(doc, "b", f"Barangay-level aggregation and reporting: export totals equaled the "
                f"database counts, including cases whose barangay is unknown, and the full "
                f"registry export contained all {cases:,} active cases.")
add_sublettered(doc, "c", f"Epidemic thresholds and alerts: the thresholds equaled an independent "
                f"recomputation in all 1,484 disease-weeks, and the Weekly Report agreed exactly "
                f"with the CESU PIDSR workbook in all 52 weeks for {len(identical)} of "
                f"{len(codes)} diseases. The remaining two differences, in measles and diphtheria, "
                f"were traced to the labeling of records in the workbook.")
add_sublettered(doc, "d", f"Hotspot detection: all {len(planted['planted'])} clusters planted in a "
                "synthetic dataset were detected, including one that crosses a barangay boundary "
                "and one in the last days of the data, with no spurious cluster and identical "
                "results on repeated runs.")
add_sublettered(doc, "e", f"Trend forecasting: forecasts were returned in at most {fc_max:.2f} "
                f"seconds and were identical on repeated requests; they are shown for "
                f"{', '.join(served)} and withheld, with the reason, for {', '.join(withheld)}, "
                "for which the model was less accurate than a same-week-last-year comparison on "
                "2024 and 2025 weeks withheld from it. In repeated four-week forecasts over the same "
                f"weeks, the dengue forecast missed by {dw['mae']:.1f} cases per week on average, "
                f"against {dw['naive_mae']:.1f} for the comparison, and identified whether the coming "
                f"weeks would rise or fall in {dw['direction_correct']} of {dw['direction_n']} forecasts, "
                "but it underestimated the size of the 2024 season. The leptospirosis forecast was less "
                "accurate than the comparison at the four-week horizon and identified the direction in "
                f"{lw['direction_correct']} of {lw['direction_n']} forecasts.")
add_sublettered(doc, "f", "Risk tiering and recommendation: every test barangay received the tier "
                "and recommendations defined by the rules, and recorded actions were preserved "
                "when a barangay's tier changed.")
add_sublettered(doc, "g", "Notifications: alerts were created once per disease, barangay, alert "
                "type, and week, contained no patient identifiers, and were delivered within one "
                "second of detection; failed deliveries were retried, and no SMS was reported as "
                "sent without a gateway.")
add_sublettered(doc, "h", "Weekly report and export: report totals matched the database, and each "
                "export was available only to its role and recorded in the audit log.")
add_sublettered(doc, "i", f"Security: all {SEC_ROUTES} protected functions refused unauthenticated requests, "
                f"all {SEC_ROLES} lower-role requests were refused, only authorized CESU personnel could "
                "enter, removal from the authorization list took effect at once, and encrypted "
                "backups were restored with every table's row count matched.")
add_para(doc, "Testing found six defects, each corrected and re-tested: cases with an unknown "
         "barangay excluded from city totals; two encephalitis syndromes merged into one disease; "
         "a disease summary that compared each barangay with the city-wide threshold; a forecast "
         "interval that changed on every request; three kinds of invalid case records accepted; "
         "and a hotspot window that skipped the most recent days of data. The end-to-end test "
         "showed that cases encoded through the system flow through hotspot detection, risk "
         "tiering, recommendation, and notification without any manual step between the modules. "
         "Plain HTTP requests to the government server are redirected to HTTPS; the page load "
         "time on the CESU office network is measured on the deployed system.")
add_numbered(doc, 4, "Evaluation of the system. [To be completed after the evaluation: the number "
             "and profile of the respondents, the weighted mean and descriptive interpretation of "
             "each ISO/IEC 25010 quality characteristic and of the overall evaluation, and the "
             "level of agreement of CESU personnel with the system's outputs.]")

# =========================================================================
add_section(doc, "", "Conclusions")
add_para(doc, "Based on the findings, the following conclusions are drawn:")
add_numbered(doc, 1, "The nine modules provide CESU with one workflow that covers the stages of "
             "outbreak management, namely detection, location, prioritization, response "
             "recommendation, and notification, which the current spreadsheet-based process does "
             "not connect.")
add_numbered(doc, 2, "The system can be built and operated entirely with open-source components on "
             "the existing government server, without licensing costs, and its email and SMS "
             "channels, recipients, and response rules can be maintained by CESU's own "
             "Administrator without programming.")
add_numbered(doc, 3, "The system meets the pass criteria of the study in every area tested before "
             "deployment. Because its Weekly Report reproduces the figures of the CESU PIDSR "
             "workbook exactly wherever the workbook's records are labeled consistently, CESU can "
             "rely on the system for its weekly reporting. Testing against independent "
             "references, namely the workbook and a dataset with known answers, revealed defects "
             "that testing the system against its own outputs would not have shown.")
add_numbered(doc, 4, "Hotspot detection identifies clusters that cross barangay boundaries, which a "
             "count within each barangay splits into parts that may each fall below the threshold. "
             "This supports the use of case-level spatial clustering alongside barangay-level "
             "thresholds.")
add_numbered(doc, 5, "The Prophet forecast, shown only where it outperforms a same-week-last-year "
             "comparison, gives CESU a reliable indication of the direction of dengue cases over "
             "the coming weeks, but not of exact counts or the size of a season, and the display "
             "check based on a single two-year test does not by itself guarantee accuracy at the "
             "four-week horizon the dashboard uses, as the leptospirosis result shows. The forecast "
             "is therefore appropriately presented as a probable trend that supports, rather than "
             "replaces, the PIDSR thresholds and the judgment of CESU personnel.")
add_numbered(doc, 6, "[Conclusion on the acceptability of the system and the agreement of CESU "
             "personnel with its outputs, to be completed after the evaluation.]")

# =========================================================================
add_section(doc, "", "Recommendations")
add_para(doc, "In light of the findings and conclusions, the following are recommended:")
add_para(doc, "For the City Epidemiology and Surveillance Unit.", bold=True, first_line_indent=0).paragraph_format.keep_with_next = True
add_lettered(doc, "a", "Review and validate the 29 draft recommendation rules using the validation "
             "sheet provided, so that the recommended response reflects CESU's own protocol.")
add_lettered(doc, "b", "Record the case classification only in the classification field and use a "
             "single label per disease (for example, “Measles” rather than "
             "“Measles Suspect”), and correct label variants such as "
             "“Diptheria”, so that counts agree across reports.")
add_lettered(doc, "c", "Enroll each staff member's authenticator application in person at the CESU "
             "office, and keep the sealed backup key and a copy of the application settings in the "
             "City Health Office safe.")
add_lettered(doc, "d", "Designate an Administrator responsible for the authorization list, the "
             "notification recipients, and the weekly review of the backup status.")
add_lettered(doc, "e", "Load each new PIDSR workbook into the system and refit the forecasting models "
             "at least monthly, so that forecasts start from recent weeks; read each forecast as a "
             "direction and a range compared with the alert and epidemic thresholds, as described "
             "in the forecast guide provided, and treat the leptospirosis forecast as background "
             "information beside rainfall, flooding, and case reports.")
add_lettered(doc, "f", "Keep a record of each four-week forecast when it is made and compare it with "
             "the counts reported for the same weeks, so that the accuracy of the deployed forecasts "
             "is checked in real time and a forecast is withheld if it stops outperforming the "
             "same-week-last-year comparison.")
add_para(doc, "For the City Health Office.", bold=True, first_line_indent=0).paragraph_format.keep_with_next = True
add_lettered(doc, "a", "Adopt the system for the weekly PIDSR reporting of CESU and use its "
             "recommended response and recorded actions in outbreak response meetings.")
add_lettered(doc, "b", "Request a CESU or City Health Office account on the Parañaque SMS API so "
             "that outbreak alerts are sent under the office's own department code.")
add_para(doc, "For the City Government of Parañaque and its ICT office.", bold=True, first_line_indent=0).paragraph_format.keep_with_next = True
add_lettered(doc, "a", "Maintain the system on the government server with HTTPS enforced, keep "
             "off-site copies of the encrypted backups, and include the system in the City's "
             "information security and data privacy reviews.")
add_lettered(doc, "b", "Consider extending the system to the other offices of the City Health "
             "Office that monitor notifiable diseases.")
add_para(doc, "For future researchers.", bold=True, first_line_indent=0).paragraph_format.keep_with_next = True
add_lettered(doc, "a", "Improve the precision of address geocoding, since only cases with a usable "
             "location can take part in hotspot detection.")
add_lettered(doc, "b", "Evaluate forecasting models that include climate and environmental "
             "variables, such as rainfall and flooding, for leptospirosis and for the diseases whose "
             "forecasts are withheld, and base the decision to display a forecast on repeated "
             "four-week tests as well as on the two-year test.")
add_lettered(doc, "c", "Assess the effect of the recommended responses on case counts over several "
             "outbreak seasons, using the action records the system keeps.")
add_lettered(doc, "d", "Replicate the system in other local government units, which can reuse its "
             "data loading and reconciliation procedures with their own PIDSR workbooks.")

doc.save(OUT)
print(f"saved {OUT}")
