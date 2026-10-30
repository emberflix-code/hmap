"""Build the two CESU explainer documents from aggregate weekly counts.

    docs/cesu_guides/HMAP_Threshold_Computation_Guide.docx
    docs/cesu_guides/HMAP_Prophet_Forecast_Guide.docx

Inputs (aggregate counts only, no case records) in docs/cesu_guides/data/:
    threshold_examples.json      city and barangay weekly counts, 2021-2026 MW1-5
    threshold_barangay_w1.json   barangay counts for MW1 2026
    prophet_accuracy.json        2-year hold-out and rolling 4-week tests
and ml/reports/prophet_eval_latest.csv.

    .venv/Scripts/python.exe docs/cesu_guides/build_cesu_guides.py
"""
import csv
import json
import statistics as st
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402
from docx import Document  # noqa: E402
from docx.enum.table import WD_TABLE_ALIGNMENT  # noqa: E402
from docx.enum.text import WD_ALIGN_PARAGRAPH  # noqa: E402
from docx.oxml import OxmlElement  # noqa: E402
from docx.oxml.ns import qn  # noqa: E402
from docx.shared import Inches, Pt, RGBColor  # noqa: E402

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"
FIG = HERE / "figures"
FIG.mkdir(exist_ok=True)
ROOT = HERE.parent.parent

BLUE, ORANGE, GREY, AMBER, RED = "#2563eb", "#ea580c", "#64748b", "#f59e0b", "#dc2626"


# ─── docx helpers ────────────────────────────────────────────────────────────

def new_doc(title, subtitle):
    d = Document()
    sec = d.sections[0]
    sec.page_width, sec.page_height = Inches(8.5), Inches(11)
    for side in ("left_margin", "right_margin", "top_margin", "bottom_margin"):
        setattr(sec, side, Inches(1))
    base = d.styles["Normal"]
    base.font.name = "Calibri"
    base.font.size = Pt(11)
    base.paragraph_format.space_after = Pt(6)
    for lvl, size in ((1, 15), (2, 12.5)):
        h = d.styles[f"Heading {lvl}"]
        h.font.name = "Calibri"
        h.font.size = Pt(size)
        h.font.color.rgb = RGBColor(0x1E, 0x3A, 0x8A)
    t = d.add_paragraph()
    r = t.add_run(title)
    r.bold = True
    r.font.size = Pt(20)
    r.font.color.rgb = RGBColor(0x1E, 0x3A, 0x8A)
    s = d.add_paragraph()
    rs = s.add_run(subtitle)
    rs.font.size = Pt(11)
    rs.font.color.rgb = RGBColor(0x47, 0x55, 0x69)
    return d


def para(d, text, bold_lead=None, italic=False, size=None):
    p = d.add_paragraph()
    if bold_lead:
        p.add_run(bold_lead).bold = True
    r = p.add_run(text)
    r.italic = italic
    if size:
        r.font.size = Pt(size)
    return p


def bullets(d, items):
    for it in items:
        p = d.add_paragraph(style="List Bullet")
        if isinstance(it, tuple):
            p.add_run(it[0]).bold = True
            p.add_run(it[1])
        else:
            p.add_run(it)


def numbered(d, items):
    for it in items:
        d.add_paragraph(it, style="List Number")


def shade(cell, hex_fill):
    tc = cell._tc.get_or_add_tcPr()
    sh = OxmlElement("w:shd")
    sh.set(qn("w:val"), "clear")
    sh.set(qn("w:color"), "auto")
    sh.set(qn("w:fill"), hex_fill)
    tc.append(sh)


def table(d, header, rows, widths=None, highlight=None, font=9.5, center=True):
    t = d.add_table(rows=1, cols=len(header))
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, h in enumerate(header):
        c = t.rows[0].cells[i]
        c.text = ""
        r = c.paragraphs[0].add_run(h)
        r.bold = True
        r.font.size = Pt(font)
        shade(c, "DBEAFE")
    for ri, row in enumerate(rows):
        cells = t.add_row().cells
        for i, v in enumerate(row):
            cells[i].text = ""
            r = cells[i].paragraphs[0].add_run(str(v))
            r.font.size = Pt(font)
            if i > 0 and center:
                cells[i].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
        if highlight and highlight(ri, row):
            for c in cells:
                shade(c, highlight(ri, row))
    # keep short tables on one page; long ones repeat the header row
    hdr = t.rows[0]._tr.get_or_add_trPr()
    rep = OxmlElement("w:tblHeader")
    rep.set(qn("w:val"), "true")
    hdr.append(rep)
    if len(rows) <= 10:
        for row in t.rows[:-1]:
            for c in row.cells:
                for p in c.paragraphs:
                    p.paragraph_format.keep_with_next = True
    if widths:
        for row in t.rows:
            for i, w in enumerate(widths):
                row.cells[i].width = Inches(w)
    d.add_paragraph()
    return t


def abbreviations(d, pairs):
    d.add_heading("Abbreviations used", 2)
    table(d, ["Abbreviation", "Meaning"], [list(p) for p in pairs], widths=[1.3, 5.2], center=False)


def figure(d, path, caption, width=6.3):
    d.add_picture(str(path), width=Inches(width))
    d.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
    c = d.add_paragraph()
    c.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = c.add_run(caption)
    r.italic = True
    r.font.size = Pt(9.5)


def formula(d, text):
    p = d.add_paragraph()
    p.paragraph_format.left_indent = Inches(0.4)
    r = p.add_run(text)
    r.font.name = "Consolas"
    r.font.size = Pt(10.5)


def style_axes(ax):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.spines["left"].set_color("#cbd5e1")
    ax.spines["bottom"].set_color("#cbd5e1")
    ax.tick_params(colors="#475569", labelsize=9)
    ax.grid(axis="y", color="#e2e8f0", linewidth=0.8)
    ax.set_axisbelow(True)


def f2(x):
    return f"{x:.2f}"


def level(n, alert, epi, single=False):
    if single:
        return "Alert (single case)" if n > 0 else "No case"
    if n > 0 and n > epi:
        return "Epidemic"
    if n > 0 and n > alert:
        return "Alert"
    return "Below alert"


LEVEL_FILL = {"Epidemic": "FECACA", "Alert": "FEF3C7"}


# ─── Document A: threshold computation ───────────────────────────────────────

def build_thresholds():
    ex = json.loads((DATA / "threshold_examples.json").read_text(encoding="utf-8"))
    w1b = json.loads((DATA / "threshold_barangay_w1.json").read_text(encoding="utf-8"))["bgy_2026_w5"]
    years = [2021, 2022, 2023, 2024, 2025]
    c1 = ex["city_2026"][0]

    # Figure: the five baseline values for MW1 with the lines they produce
    fig, ax = plt.subplots(figsize=(7.2, 3.3), dpi=200)
    labels = [str(y) for y in years] + ["2026"]
    vals = c1["baseline"] + [c1["current"]]
    ax.bar(labels, vals, color=[BLUE] * 5 + [RED], width=0.62)
    for i, v in enumerate(vals):
        ax.text(i, v + 0.8, str(v), ha="center", fontsize=9, color="#1e293b")
    for y, col, ls, name in ((c1["mean"], GREY, "--", "5-year mean"),
                             (c1["alert"], AMBER, "--", "Alert threshold (mean + 1 SD)"),
                             (c1["epidemic"], RED, ":", "Epidemic threshold (mean + 2 SD)")):
        ax.hlines(y, -0.6, 5.38, color=col, ls=ls, lw=1.6)
        ax.text(5.48, y, f"{name}  {y:.2f}", va="center", fontsize=8.5, color="#334155")
    ax.set_xlim(-0.6, 8.4)
    ax.set_ylabel("Dengue cases, MW1 (Confirmed + Probable)", fontsize=9, color="#475569")
    style_axes(ax)
    fig.tight_layout()
    fig.savefig(FIG / "threshold_mw1.png")
    plt.close(fig)

    d = new_doc("How H-MAP Computes the Alert and Epidemic Thresholds",
                "A worked example using Parañaque City PIDSR data · For the City Epidemiology and Surveillance Unit (CESU)")

    abbreviations(d, [
        ("PIDSR", "Philippine Integrated Disease Surveillance and Response"),
        ("CESU", "City Epidemiology and Surveillance Unit"),
        ("DOH", "Department of Health"),
        ("MW", "Morbidity week (the PIDSR reporting week, MW1 to MW52 or MW53)"),
        ("SD", "Standard deviation (how spread out the five baseline counts are)"),
        ("AFP", "Acute flaccid paralysis"),
        ("5YrAve", "The five-year average sheet in the CESU PIDSR workbook"),
    ])
    d.add_heading("1. What the thresholds are for", 1)
    para(d, "H-MAP marks a disease week as unusual when its case count is higher than what the same week "
            "normally looks like in Parañaque. \"Normal\" is measured from the city's own records of the five "
            "previous years. Two lines are drawn from those records, following the PIDSR Manual of Procedures "
            "(Department of Health, 2014, pp. 57-58):")
    bullets(d, [("Alert threshold = mean + 1 standard deviation. ", "Crossing it means the week is higher than usual "
                 "and should be watched."),
                ("Epidemic threshold = mean + 2 standard deviations. ", "Crossing it means the week is well above "
                 "the usual range and may need a response."),
                ("Single-case diseases (Measles, AFP). ", "One case is already an alert, whatever the baseline says.")])

    d.add_heading("2. The rule, step by step", 1)
    numbered(d, [
        "Pick the disease and the morbidity week (MW) to check, for example Dengue, MW1 of 2026.",
        "Count the Confirmed and Probable cases for that same MW in each of the 5 previous years "
        "(2021 to 2025). Suspect, Discarded and other classifications are not counted. A year with no cases counts as 0.",
        "Compute the mean (average) of the 5 counts.",
        "Compute the standard deviation (SD) of the 5 counts using the sample formula (divide by 4, that is n - 1). "
        "This is Excel's STDEV.S.",
        "Alert threshold = mean + SD. Epidemic threshold = mean + 2 x SD.",
        "Compare the current week's Confirmed + Probable count. A count greater than the epidemic threshold is "
        "an epidemic-level week; greater than the alert threshold (but not the epidemic one) is an alert-level week.",
    ])
    para(d, "The baseline moves every year: for weeks of 2026 it is 2021 to 2025, for weeks of 2027 it will be "
            "2022 to 2026. Each morbidity week has its own pair of thresholds, so a rainy-season week is compared "
            "with past rainy-season weeks, not with the dry months.")

    d.add_heading("3. Worked example: Dengue, city-wide, MW1 of 2026", 1)
    para(d, "Confirmed + Probable dengue cases in MW1 of each baseline year:")
    devs = [v - c1["mean"] for v in c1["baseline"]]
    rows = [[str(y), v, f"{dv:+.1f}", f"{dv * dv:.2f}"] for y, v, dv in zip(years, c1["baseline"], devs)]
    rows.append(["Total", sum(c1["baseline"]), "0.0", f"{sum(x * x for x in devs):.2f}"])
    table(d, ["Year", "Cases in MW1", "Difference from mean", "Difference squared"], rows,
          widths=[1.2, 1.4, 1.9, 1.9], highlight=lambda i, r: "F1F5F9" if r[0] == "Total" else None)
    ss = sum(x * x for x in devs)
    formula(d, f"Mean      = {sum(c1['baseline'])} / 5 = {c1['mean']:.1f}")
    formula(d, f"Variance  = {ss:.2f} / (5 - 1) = {ss / 4:.2f}")
    formula(d, f"SD        = square root of {ss / 4:.2f} = {c1['sd']:.2f}")
    formula(d, f"Alert     = {c1['mean']:.1f} + {c1['sd']:.2f} = {c1['alert']:.2f}")
    formula(d, f"Epidemic  = {c1['mean']:.1f} + 2 x {c1['sd']:.2f} = {c1['epidemic']:.2f}")
    para(d, f"MW1 of 2026 had {c1['current']} Confirmed + Probable dengue cases. {c1['current']} is greater than "
            f"{c1['epidemic']:.2f}, so the week is at the epidemic level and H-MAP shows it in red.",
         bold_lead="Result. ")
    figure(d, FIG / "threshold_mw1.png",
           "Figure 1. MW1 dengue counts for the five baseline years (blue) and 2026 (red), with the lines they produce.")
    para(d, "These are the same numbers H-MAP stores in its thresholds table: mean 17.2000, SD 7.8549, epidemic "
            "threshold 32.9099, baseline years 2021 to 2025. The hand computation and the system agree to four "
            "decimal places for every week shown in the next section.", italic=True)

    d.add_heading("4. The first five weeks of 2026", 1)
    para(d, "The same steps repeated for MW1 to MW5 give three different outcomes:")
    rows = []
    for c in ex["city_2026"]:
        rows.append([f"MW{c['week']}", ", ".join(map(str, c["baseline"])), f"{c['mean']:.1f}", f2(c["sd"]),
                     f2(c["alert"]), f2(c["epidemic"]), c["current"], level(c["current"], c["alert"], c["epidemic"])])
    table(d, ["Week", "2021-2025 counts", "Mean", "SD", "Alert", "Epidemic", "2026", "Level"], rows,
          widths=[0.6, 1.5, 0.6, 0.65, 0.7, 0.8, 0.55, 1.0],
          highlight=lambda i, r: LEVEL_FILL.get(r[-1]))
    bullets(d, [
        ("MW1 (43 cases): epidemic level. ", "Far above a baseline that was mostly in the teens and twenties."),
        ("MW4 (38 cases): alert level. ", "Above 35.54 but below 50.09."),
        ("MW2 (32 cases): below alert, even though 32 is a lot of cases. ", "The 2025 baseline year had 46 cases in "
         "MW2 and 55 in MW3, which raised both the mean and the SD. An outbreak year in the baseline makes the "
         "thresholds higher for the next five years. The CESU should keep this in mind when 2025 is in the baseline."),
        ("MW5 (5 cases): below alert, but probably incomplete. ", "MW5 is the latest week in the workbook, and late "
         "reports are still arriving. The most recent one or two weeks always look lower than they will end up."),
    ])

    d.add_heading("5. Barangay example: San Isidro, MW1 of 2026", 1)
    sib = next(b for b in w1b if b["barangay"] == "San Isidro")
    devs = [v - sib["mean"] for v in sib["baseline"]]
    ss = sum(x * x for x in devs)
    para(d, "H-MAP repeats the same computation for each barangay, using only that barangay's cases. This is what "
            "drives the \"above epidemic threshold\" reason in the barangay risk tiers on the dashboard.")
    formula(d, f"Baseline (2021-2025)  = {', '.join(map(str, sib['baseline']))}")
    formula(d, f"Mean                  = {sum(sib['baseline'])} / 5 = {sib['mean']:.1f}")
    formula(d, f"Variance              = {ss:.2f} / 4 = {ss / 4:.2f}")
    formula(d, f"SD                    = {sib['sd']:.4f}")
    formula(d, f"Alert                 = {sib['alert']:.2f}")
    formula(d, f"Epidemic              = {sib['epidemic']:.2f}")
    para(d, f"San Isidro had {sib['current']} cases in MW1 of 2026, well above {sib['epidemic']:.2f}: epidemic level.",
         bold_lead="Result. ")
    para(d, "All 16 barangays for the same week (the 2026 counts add up to the city total of 43):")
    rows = []
    for b in w1b:
        rows.append([b["barangay"], ", ".join(map(str, b["baseline"])), f"{b['mean']:.1f}", f2(b["alert"]),
                     f2(b["epidemic"]), b["current"], level(b["current"], b["alert"], b["epidemic"])])
    table(d, ["Barangay", "2021-2025", "Mean", "Alert", "Epidemic", "2026", "Level"], rows,
          widths=[1.7, 1.2, 0.6, 0.7, 0.8, 0.55, 1.0], highlight=lambda i, r: LEVEL_FILL.get(r[-1]), font=9)
    para(d, "When a barangay's baseline is very small the thresholds are very low. Vitalez had no MW1 dengue cases "
            "in any baseline year, so its thresholds are 0 and its single case puts it at the epidemic level. Don Galo "
            "(baseline 1, 0, 0, 0, 0) reaches the epidemic level with 3 cases. These flags are correct by the rule, "
            "but one or two cases in a small barangay are weaker evidence than seven cases in San Isidro. H-MAP "
            "requires at least one case before it flags a barangay, and it raises a barangay to High risk only "
            "when an active hotspot (200 m, 3 or more cases, 4 weeks) is also present.",
         bold_lead="Small numbers need judgment. ")

    d.add_heading("6. Single-case diseases: Measles and AFP", 1)
    mea = ex["single"]["MEA"]
    b3 = mea["baseline_w"]["3"]
    m3, s3 = st.mean(b3), st.stdev(b3)
    para(d, "For Measles and Acute Flaccid Paralysis, the PIDSR rule is that one case is already an alert "
            "(DOH, 2014, p. 58). The mean + SD lines are hidden for these diseases on the dashboard. The example "
            "below shows why the formula alone would not work.")
    formula(d, f"Measles, MW3 baseline (2021-2025) = {', '.join(map(str, b3))}")
    formula(d, f"Mean = {m3:.1f}   SD = {s3:.3f}   Epidemic threshold = {m3 + 2 * s3:.2f}")
    para(d, f"Suppose one measles case is reported in MW3. By the formula, 1 is below {m3 + 2 * s3:.2f}, so it would "
            "not be flagged. By the single-case rule it is flagged at once, which is what H-MAP does. (This is an "
            "illustration: there were no Confirmed or Probable measles or AFP cases in MW1 to MW5 of 2026.)")

    d.add_heading("7. How this differs from the 5YrAve sheet in the PIDSR workbook", 1)
    cy = ex["cesu_ytd"]
    py = cy["per_year"]
    para(d, "The CESU workbook's 5YrAve sheet answers a different question, so its numbers will not match the "
            "H-MAP thresholds:")
    table(d, ["", "5YrAve sheet (workbook)", "H-MAP PIDSR thresholds"], [
        ["Period", "Cumulative, MW1 up to the selected week", "One morbidity week"],
        ["Classifications", "All (including Suspect)", "Confirmed + Probable only"],
        ["Statistic", "Average and median", "Mean, SD, mean + 1 SD, mean + 2 SD"],
        ["Purpose", "Reference value for the memo", "Alert and epidemic signal"],
    ], widths=[1.3, 2.6, 2.6], center=False)
    avg = sum(py.values()) / 5
    para(d, f"Example, dengue up to MW5: the cumulative MW1-5 totals for 2021 to 2025 (all classifications) are "
            f"{', '.join(str(py[str(y)]) for y in years)}. Their average is {avg:.1f}, which is the value in the "
            f"5YrAve sheet. The 2026 cumulative total is {cy['current']} ({cy['current_cp']} Confirmed + Probable). "
            "H-MAP shows the 5YrAve reference on the Weekly Report and uses the PIDSR thresholds for alerts.")

    d.add_heading("8. Checking a threshold yourself in Excel", 1)
    para(d, "Put the five baseline counts in cells B2 to F2 (for example 23, 6, 24, 12, 21) and use:")
    table(d, ["Cell", "Formula", "Result for Dengue MW1"], [
        ["G2 (mean)", "=AVERAGE(B2:F2)", "17.20"],
        ["H2 (SD)", "=STDEV.S(B2:F2)", "7.85"],
        ["I2 (alert)", "=G2+H2", "25.05"],
        ["J2 (epidemic)", "=G2+2*H2", "32.91"],
    ], widths=[1.4, 2.4, 2.0])
    para(d, "Use STDEV.S, not STDEV.P. STDEV.P divides by 5 instead of 4 and gives slightly lower thresholds "
            "(7.03 instead of 7.85 for this example, so an epidemic threshold of 31.25 instead of 32.91).")

    d.add_heading("9. Where the thresholds appear in H-MAP", 1)
    bullets(d, [
        ("Dashboard, weekly trend chart: ", "the dashed lines are the 5-year mean, alert and epidemic thresholds. "
         "Use the Line / Histogram switch to see the weeks as a line or as bars (an epidemic curve). Weeks above the "
         "alert threshold are amber and weeks above the epidemic threshold are red in both views."),
        ("Dashboard, summary cards and barangay risk tiers: ", "the per-barangay computation in Section 5."),
        ("Weekly Report: ", "PIDSR level per disease next to the 5YrAve reference."),
        ("Alerts menu: ", "a notification when a barangay crosses its epidemic threshold."),
    ])
    para(d, "Reference: Department of Health. (2014). Manual of procedures for the Philippine Integrated Disease "
            "Surveillance and Response (3rd ed.). Epidemiology Bureau.", size=9.5)

    out = HERE / "HMAP_Threshold_Computation_Guide.docx"
    d.save(out)
    print(out)


# ─── Document B: Prophet forecast ────────────────────────────────────────────

def build_prophet():
    acc = json.loads((DATA / "prophet_accuracy.json").read_text(encoding="utf-8"))
    with open(ROOT / "ml" / "reports" / "prophet_eval_latest.csv", encoding="utf-8-sig") as fh:
        ev = list(csv.DictReader(fh))
    for r in ev:
        r["barangay_name"] = r["barangay_name"].encode("latin-1", "ignore").decode("utf-8", "ignore") \
            if "Ã" in r["barangay_name"] else r["barangay_name"]

    den = acc["DENGUE"]
    ty = den["two_year"]
    ds = pd.to_datetime(ty["ds"])

    # Figure 1: two-year hold-out, dengue city-wide
    fig, ax = plt.subplots(figsize=(7.4, 3.4), dpi=200)
    ax.fill_between(ds, ty["lo"], ty["hi"], color=ORANGE, alpha=0.15, lw=0, label="Prophet 80% range")
    ax.plot(ds, ty["naive"], color=GREY, lw=1, ls="--", label="Same week last year")
    ax.plot(ds, ty["actual"], color=BLUE, lw=2, label="Actual cases")
    ax.plot(ds, ty["yhat"], color=ORANGE, lw=2, label="Prophet forecast")
    ax.set_ylabel("Dengue cases per week", fontsize=9, color="#475569")
    ax.set_ylim(bottom=0)
    style_axes(ax)
    ax.legend(fontsize=8, frameon=False, ncol=4, loc="upper center", bbox_to_anchor=(0.5, 1.13))
    fig.tight_layout()
    fig.savefig(FIG / "prophet_holdout_dengue.png")
    plt.close(fig)

    # Figure 2: rolling 4-week-ahead forecasts, dengue city-wide
    ro = pd.DataFrame(den["rolling4"]["rows"])
    ro["ds"] = pd.to_datetime(ro["ds"])
    fig, ax = plt.subplots(figsize=(7.4, 3.4), dpi=200)
    first = True
    for k in range(0, len(ro), 4):
        blk = ro.iloc[k:k + 4]
        ax.fill_between(blk["ds"], blk["lo"], blk["hi"], color=ORANGE, alpha=0.15, lw=0,
                        label="Prophet 80% range" if first else None)
        ax.plot(blk["ds"], blk["yhat"], color=ORANGE, lw=2, label="4-week forecast" if first else None)
        first = False
    ax.plot(ro["ds"], ro["actual"], color=BLUE, lw=2, label="Actual cases")
    ax.set_ylabel("Dengue cases per week", fontsize=9, color="#475569")
    ax.set_ylim(bottom=0)
    style_axes(ax)
    ax.legend(fontsize=8, frameon=False, ncol=3, loc="upper center", bbox_to_anchor=(0.5, 1.13))
    fig.tight_layout()
    fig.savefig(FIG / "prophet_rolling_dengue.png")
    plt.close(fig)

    d = new_doc("How H-MAP Forecasts Cases with Prophet",
                "How the forecast works, how the CESU should read it, and how accurate it has been on Parañaque data")

    abbreviations(d, [
        ("MAPE", "Mean Absolute Percentage Error (average miss per week, in percent)"),
        ("RMSE", "Root Mean Square Error (typical miss per week, in cases)"),
        ("MAE", "Mean Absolute Error (average miss per week, in cases)"),
        ("ILI", "Influenza-like illness"),
        ("HFMD", "Hand, foot and mouth disease"),
        ("TYP / LEP", "Typhoid / Leptospirosis"),
        ("CESU", "City Epidemiology and Surveillance Unit"),
    ])
    d.add_heading("1. In one paragraph", 1)
    para(d, "H-MAP uses a forecasting method called Prophet (Taylor & Letham, 2018) to estimate the number of "
            "Confirmed + Probable cases for the next four weeks. It learns two things from the city's weekly counts "
            "since 2010: the long-run level of the disease and its usual pattern through the year (for dengue, the "
            "rise in the rainy months). The forecast is a likely direction and range, not an exact count. It is "
            "shown only for diseases where it has proven better than simply repeating last year's numbers, and it "
            "is one input to the CESU's judgment, never a replacement for it.")

    d.add_heading("2. How the forecast is made", 1)
    numbered(d, [
        "Weekly counts. Confirmed and Probable cases are added up per morbidity week, from 2010 to the latest "
        "training data (the same case definition as the thresholds). Weeks with no cases count as 0.",
        "Trend. Prophet fits a slowly changing line through the years: is the disease generally becoming more or "
        "less common?",
        "Yearly pattern. Prophet learns how each part of the year compares with the trend, for example that "
        "the rainy months are usually much higher than the dry months for dengue. The pattern is multiplied by "
        "the trend, so in a high year the rainy-season peak is higher too.",
        "Forecast. Trend times yearly pattern, carried forward four weeks, gives the predicted cases for each week.",
        "Range. Prophet also gives an 80% range (lower and upper bound). In principle, about 4 out of 5 future "
        "weeks should fall inside it. Section 5 shows how well that held on Parañaque data.",
    ])
    para(d, "What the model does not know: floods and typhoons, clean-up drives, school calendars, outbreaks in "
            "nearby cities, changes in reporting, or anything that has not happened in a regular yearly pattern "
            "before. These are exactly the things the CESU knows and the model does not.")

    d.add_heading("3. When H-MAP shows a forecast and when it does not", 1)
    para(d, "Before a forecast is shown, H-MAP tests it. The model is trained on 2010 to 2023 only, asked to "
            "predict 2024 and 2025, and compared with what actually happened. The same test is given to the "
            "simplest possible guess: the same week last year. If Prophet does not beat that guess, the forecast is "
            "withheld and the dashboard says so.")
    city = [r for r in ev if r["barangay_name"] == "city-wide"]
    names = {"DENGUE": "Dengue", "TYP": "Typhoid", "LEP": "Leptospirosis", "ILI": "Influenza-like illness",
             "MEA": "Measles", "HFMD": "Hand, foot and mouth disease"}
    rows = []
    for r in city:
        mp, mb = float(r["mape_prophet"]), float(r["mape_baseline"])
        rows.append([names.get(r["disease"], r["disease"]), f"{mp:.1f}%", f"{mb:.1f}%",
                     f"{float(r['rmse_prophet']):.2f}", f"{float(r['rmse_baseline']):.2f}",
                     "Shown" if mp < mb else "Withheld"])
    table(d, ["Disease (city-wide)", "Prophet error (MAPE)", "Last-year error (MAPE)", "Prophet RMSE",
              "Last-year RMSE", "On the dashboard"], rows, widths=[1.7, 1.0, 1.0, 0.9, 0.9, 1.0],
          highlight=lambda i, r: "F1F5F9" if r[-1] == "Withheld" else None)
    para(d, "What the columns mean:", bold_lead=None).runs[0].bold = True
    bullets(d, [
        ("MAPE (Mean Absolute Percentage Error): ", "the average miss per week, as a percentage of the actual "
         "count. H-MAP adds 1 to the actual count before dividing, so weeks with 0 cases do not make the "
         "percentage infinite. Example: 40 actual cases and a forecast of 30 is a miss of 10 / (40 + 1) = 24.4%."),
        ("RMSE (Root Mean Square Error): ", "the typical miss in number of cases per week. Each week's miss is "
         "squared, averaged, then square-rooted, so one large miss counts more than several small ones. "
         "Example: misses of 2 and 4 cases give the square root of (4 + 16) / 2 = 3.16 cases."),
        ("Prophet error: ", "how far the H-MAP forecast was from the actual weekly counts in 2024 and 2025."),
        ("Last-year error: ", "how far the simple guess \"same week last year\" (also called the seasonal-naive "
         "forecast) was from the same actual counts."),
        ("On the dashboard: ", "\"Shown\" when Prophet's MAPE is lower than the last-year MAPE, otherwise "
         "\"Withheld\". For both measures, lower is better."),
        ("ILI: ", "Influenza-like illness."),
        ("HFMD: ", "Hand, foot and mouth disease."),
        ("City-wide: ", "all 16 barangays counted together."),
    ])
    para(d, "Why three diseases are withheld: Measles and HFMD have mostly zero weeks with occasional bursts, and "
            "influenza-like illness depends on which strains circulate in a given year. None of them follows a "
            "regular yearly pattern that Prophet can learn, so for these the CESU should rely on the thresholds and "
            "the single-case rule.")

    d.add_heading("4. How the CESU should read the forecast", 1)
    bullets(d, [
        ("Read the direction first. ", "Is the line going up, flat or down over the four weeks? H-MAP calls a "
         "barangay's forecast \"rising\" when the fourth week is at least 10% and at least one case higher than "
         "the first. A rising forecast alone puts a barangay at Moderate risk."),
        ("Then read the range, not the single number. ", "\"About 50 to 80 cases next week\" is the honest "
         "message; \"63 cases\" is not."),
        ("Compare the range with the thresholds. ", "If the upper bound reaches the alert threshold for the "
         "coming weeks, prepare (supplies, information drives, search-and-destroy scheduling). If the forecast "
         "itself is above the epidemic threshold, treat it as an early warning and verify with the latest reports."),
        ("Check the latest weeks. ", "The last one or two reported weeks are usually incomplete because of late "
         "reports, so actual counts often look low at first. Do not conclude that the forecast is too high until "
         "those weeks have filled in."),
        ("Add what the model cannot see. ", "After heavy rains or flooding, expect leptospirosis and dengue to run "
         "above the forecast. After a strong vector control campaign, expect dengue below it."),
        ("Note the model's freshness. ", "The forecast is anchored to the current week, but the model only "
         "knows the data it was trained on (currently up to December 2025). Retrain it whenever a newer PIDSR "
         "workbook is loaded (python ml/train_prophet.py), ideally monthly, so the forecast starts from recent weeks."),
    ])
    table(d, ["What the forecast shows", "Suggested reading"], [
        ["Flat or falling, well below the alert line", "Routine surveillance."],
        ["Rising, upper bound near or above the alert line", "Prepare and watch the next reports closely."],
        ["Forecast above the epidemic line", "Early warning. Verify with current case reports and hotspots."],
        ["Forecast withheld", "Use thresholds, the single-case rule and hotspots only."],
    ], widths=[3.0, 3.4], center=False)

    d.add_heading("5. How accurate it has been on Parañaque data", 1)
    d.add_heading("5.1 Two-year test (the display check)", 2)
    para(d, f"Figure 1 shows the test from Section 3 for dengue: one forecast made at the end of 2023 for every "
            f"week of 2024 and 2025. Prophet caught the timing of both rainy seasons and missed less than the "
            f"same-week-last-year guess (RMSE 20.2 against 27.6 cases per week). It did not foresee the size "
            f"of the 2024 season: actual cases reached about {max(ty['actual'][:52]):.0f} a week while the forecast "
            f"peaked near {max(ty['yhat'][:52]):.0f}. A forecast made far ahead knows when the season comes, "
            f"not how big it will be. "
            f"{ty['coverage80'] * 100:.0f}% of the actual weeks fell inside the 80% range, so the range is somewhat "
            "narrower than it claims: treat it as the typical range, not a guarantee.")
    figure(d, FIG / "prophet_holdout_dengue.png",
           "Figure 1. Dengue, city-wide: actual weekly cases in 2024-2025 against a forecast made at the end of 2023.")

    d.add_heading("5.2 Four-week test (how the dashboard is used)", 2)
    para(d, "The dashboard shows only the next four weeks, from a model that has seen all earlier data. To test "
            "exactly that, the model was retrained every four weeks through 2024 and 2025, each time forecasting "
            "the next four weeks only, and compared with what happened.")
    rows = []
    for code in ("DENGUE", "TYP", "LEP"):
        r4 = acc[code]["rolling4"]
        rows.append([names[code], f"{r4['mae']:.1f}", f"{r4['naive_mae']:.1f}", f"{r4['mape']:.1f}%",
                     f"{r4['naive_mape']:.1f}%", f"{r4['coverage80'] * 100:.0f}%",
                     f"{round(r4['direction_agree'] * r4['n_direction'])} of {r4['n_direction']}"])
    table(d, ["Disease", "Avg miss, Prophet (cases/wk)", "Avg miss, last year (cases/wk)", "Prophet MAPE",
              "Last-year MAPE", "Weeks inside 80% range", "Direction correct"], rows,
          widths=[1.1, 1.0, 1.0, 0.85, 0.85, 0.9, 0.9], font=9)
    r4 = den["rolling4"]
    act = pd.Series(ty["actual"])
    para(d, f"Dengue. Over 2024-2025 the city averaged {act.mean():.0f} dengue cases a week (lowest {act.min():.0f}, "
            f"highest {act.max():.0f}). The four-week forecast missed by {r4['mae']:.1f} cases a week on average, "
            f"against {r4['naive_mae']:.1f} for the last-year guess, and it called the direction of the next four "
            f"weeks (up or down from the previous four) correctly {round(r4['direction_agree'] * r4['n_direction'])} "
            f"times out of {r4['n_direction']}. The one-week-ahead forecast was the most accurate "
            f"(MAPE {r4['by_h']['1']['mape']:.0f}%, against {r4['by_h']['4']['mape']:.0f}% four weeks ahead). "
            "This is the strongest result and the main use of the forecast. Figure 2 also shows its typical "
            "mistake: in 2024 it followed the rise but stayed below the peak, and in 2025, having just seen a "
            "large season, it expected another one and ran above the actual counts. The forecast tends to repeat "
            "the size of recent seasons; the threshold lines and the current reports show whether this season "
            "is different.")
    figure(d, FIG / "prophet_rolling_dengue.png",
           "Figure 2. Dengue, city-wide: each orange segment is a 4-week forecast made with the data available at the time.")
    t4, l4 = acc["TYP"]["rolling4"], acc["LEP"]["rolling4"]
    para(d, f"Typhoid. Small but consistent gain over the last-year guess (average miss {t4['mae']:.1f} against "
            f"{t4['naive_mae']:.1f} cases a week). With only one or two cases a week, the direction is often a "
            "matter of a single case, so read typhoid forecasts as \"low and steady\" or \"higher than usual\" only.")
    para(d, f"Leptospirosis: read with caution. Leptospirosis passes the two-year check, but in the four-week test "
            f"it did worse than the last-year guess (average miss {l4['mae']:.2f} against {l4['naive_mae']:.2f} cases "
            f"a week) and called the direction correctly only {round(l4['direction_agree'] * l4['n_direction'])} times "
            f"out of {l4['n_direction']}, about as often as a coin toss. Leptospirosis follows floods, which "
            "a yearly pattern cannot predict. Until the display check also uses the four-week test, the CESU should "
            "treat the leptospirosis forecast as background information and act on rainfall, flooding and case "
            "reports instead.")

    d.add_heading("5.3 Barangay-level dengue forecasts", 2)
    bg = [r for r in ev if r["disease"] == "DENGUE" and r["barangay_name"] != "city-wide"]
    bg.sort(key=lambda r: float(r["mape_prophet"]))
    rows = [[r["barangay_name"], f"{float(r['mape_prophet']):.1f}%", f"{float(r['mape_baseline']):.1f}%",
             f"{float(r['rmse_prophet']):.2f}", f"{float(r['rmse_baseline']):.2f}"] for r in bg]
    table(d, ["Barangay", "Prophet MAPE", "Last-year MAPE", "Prophet RMSE", "Last-year RMSE"], rows,
          widths=[2.0, 1.1, 1.1, 1.1, 1.1], font=9,
          highlight=lambda i, r: "FEF3C7" if float(r[3]) > float(r[4]) else None)
    para(d, "All 15 barangays with enough dengue cases beat the last-year guess on MAPE, so their forecasts are "
            "shown. In the highlighted barangays, Prophet's RMSE is slightly worse: it misses the occasional large "
            "week by more, even though it is closer on ordinary weeks. Barangay forecasts work with a few cases a "
            "week, so they are best read for direction.")

    d.add_heading("6. Summary for the CESU", 1)
    bullets(d, [
        "The forecast is reliable enough to watch the direction of dengue over the next four weeks, and it is "
        "closest one week ahead.",
        "Read the range and the direction, and compare them with the alert and epidemic thresholds; do not quote "
        "the single predicted number.",
        "Typhoid forecasts are modestly useful; leptospirosis forecasts should not drive decisions on their own.",
        "Measles, ILI and HFMD forecasts are withheld on purpose; use the thresholds and the single-case rule.",
        "Retrain the model whenever new workbook data is loaded, and always add local knowledge (weather, "
        "campaigns, reporting delays) that the model cannot see.",
    ])
    para(d, "Notes on the figures. The display-check figures in Section 3 come from the stored evaluation "
            "(ml/reports/prophet_eval_latest.csv). The four-week test and Figures 1 and 2 were rerun on the "
            "current database for this guide; the dengue two-year error there is "
            f"{ty['mape']:.1f}% (stored value 50.1%). The small difference comes from the reloaded case data.",
         size=9.5, italic=True)
    para(d, "Reference: Taylor, S. J., & Letham, B. (2018). Forecasting at scale. The American Statistician, "
            "72(1), 37-45. https://doi.org/10.1080/00031305.2017.1380080", size=9.5)

    out = HERE / "HMAP_Prophet_Forecast_Guide.docx"
    d.save(out)
    print(out)


if __name__ == "__main__":
    build_thresholds()
    build_prophet()
