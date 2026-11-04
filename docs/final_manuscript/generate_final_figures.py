"""Generates the Chapter 2-3 figures for the final revision manuscript.

Every figure is drawn at its printed size (6.0 in wide, the text block of the
TUP Letter format), one data unit = one inch, so font sizes here are the sizes
that appear on paper. Keep body text at 6.5 pt or larger.

fig01_ipo.png            Figure 1. Conceptual Model (Input-Process-Output)
fig03_use_case.png       Figure 2. Use Case Diagram («include» / «extend»)
fig02_architecture.png   Figure 3. System Architecture
fig04_outbreak_flow.png  Figure 4. Outbreak Management Flow
"""
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse, FancyArrowPatch, FancyBboxPatch, Rectangle

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "figures")
os.makedirs(OUT, exist_ok=True)
plt.rcParams["font.family"] = "Times New Roman"
INK, BLUE, AMBER, FILL, SOFT = "#1f2937", "#1d4ed8", "#b45309", "#eef2ff", "#f8fafc"
WIDTH = 6.0


def canvas(height):
    fig = plt.figure(figsize=(WIDTH, height))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, WIDTH)
    ax.set_ylim(0, height)
    ax.axis("off")
    return fig, ax


def save(fig, name):
    fig.savefig(os.path.join(OUT, name), dpi=300, facecolor="white")
    plt.close(fig)
    print("saved", name)


def rbox(ax, x, y, w, h, fill, lw=0.9):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.0,rounding_size=0.06",
                                fc=fill, ec=INK, lw=lw))


def arrow(ax, p1, p2, dashed=False, color=INK, rad=0.0, lw=0.9, head=8):
    ax.add_patch(FancyArrowPatch(p1, p2, arrowstyle="-|>", mutation_scale=head, color=color,
                                 lw=lw, linestyle=(0, (3, 2)) if dashed else "-",
                                 connectionstyle=f"arc3,rad={rad}", shrinkA=1, shrinkB=1))


# --- Figure 1: IPO ------------------------------------------------------------
def ipo():
    fig, ax = canvas(3.15)
    cols =[(0.02, "INPUT", FILL, 7.0, [
        "Knowledge Requirements",
        "  • PIDSR alert and epidemic thresholds",
        "  • CESU cluster rule (200 m, 3 cases,",
        "     4 weeks); DBSCAN; Prophet",
        "  • CESU and DOH response protocol",
        "  • ISO/IEC 25010:2023; RA 10173",
        "Software Requirements",
        "  • PHP 7.4, Laravel 8, MySQL 8",
        "  • Python 3.8, FastAPI, scikit-learn,",
        "     Prophet",
        "  • React, Leaflet.js, Chart.js",
        "  • SMS gateway; email service",
        "Data Requirements",
        "  • PIDSR records, 2010 to 2026",
        "  • 29 diseases, 16 barangays",
        "  • Populations; OpenStreetMap",
        "Infrastructure Requirements",
        "  • DICT server; HRMO portal",
    ]), (2.04, "PROCESS", "#ecfdf5", 7.5, [
        "1. Requirements analysis",
        "    and consultation with",
        "    the CESU",
        "2. Design: use cases,",
        "    database, architecture,",
        "    and rules",
        "3. Iterative development",
        "    of the nine modules",
        "4. Testing against",
        "    measurable criteria",
        "5. Authorization, consent,",
        "    ISO/IEC 25010",
        "    evaluation, and CESU",
        "    output validation",
    ]), (4.06, "OUTPUT", "#fff7ed", 7.5, [
        "Web-Based Disease",
        "Outbreak Management",
        "System for the City",
        "Epidemiology and",
        "Surveillance Unit",
        "",
        "  • Deployed on the",
        "     government server",
        "  • Documented test results",
        "  • Evaluation and output",
        "     validation results",
        "  • Documentation and",
        "     turnover to CHO-HIMU",
    ])]
    w, y0, h = 1.92, 0.55, 2.55
    for x, title, fill, size, lines in cols:
        rbox(ax, x, y0, w, h, fill)
        ax.text(x + w / 2, y0 + h - 0.12, title, ha="center", va="top", fontsize=9,
                fontweight="bold", color=INK)
        ax.text(x + 0.08, y0 + h - 0.42, "\n".join(lines), ha="left", va="top", fontsize=size,
                color=INK, linespacing=1.35)
    mid = y0 + h / 2
    arrow(ax, (0.02 + w, mid), (2.04, mid), lw=1.4, head=11)
    arrow(ax, (2.04 + w, mid), (4.06, mid), lw=1.4, head=11)
    arrow(ax, (5.02, 0.53), (3.0, 0.53), dashed=True, rad=-0.3, lw=1.0, head=9)
    ax.text(4.0, 0.02, "Feedback from testing and evaluation", ha="center", va="bottom",
            fontsize=7, style="italic", color=INK)
    save(fig, "fig01_ipo.png")


# --- Figure 2: Use case diagram -------------------------------------------------
def stick(ax, x, y, label):
    ax.add_patch(plt.Circle((x, y + 0.27), 0.075, fc="white", ec=INK, lw=0.9))
    ax.plot([x, x], [y + 0.195, y - 0.04], color=INK, lw=0.9)
    ax.plot([x - 0.13, x + 0.13], [y + 0.12, y + 0.12], color=INK, lw=0.9)
    ax.plot([x, x - 0.11], [y - 0.04, y - 0.22], color=INK, lw=0.9)
    ax.plot([x, x + 0.11], [y - 0.04, y - 0.22], color=INK, lw=0.9)
    ax.text(x, y - 0.29, label, ha="center", va="top", fontsize=7.5, fontweight="bold")


def use_case():
    fig, ax = canvas(7.62)
    ax.add_patch(Rectangle((0.86, 0.32), 4.06, 7.22, fc="white", ec=INK, lw=1.0))
    ax.text(2.89, 7.44, "Web-Based Disease Outbreak Management System", ha="center",
            va="top", fontsize=8.5, fontweight="bold")

    A, B, WA, WB, H = 1.98, 4.0, 1.78, 1.62, 0.5

    def y(old):  # rows spaced 0.64 in apart, bottom row (1.1) at 0.75 in
        return 0.75 + 0.8 * (old - 1.1)

    # Prioritize/Recommend sits between Monitor and Detect, and Send sits level
    # with it, so every relationship is a short arrow with no crossings.
    PR = "Prioritize Barangays\nand Recommend\nResources"
    pos = {
        "Encode Case Record": (A, y(8.3)), "Import Case Records": (A, y(7.5)),
        "Monitor Epidemic\nThresholds": (A, y(6.7)), PR: (A, y(5.9)),
        "Detect Hotspots": (A, y(5.1)), "View Trend Forecast": (A, y(4.3)),
        "Generate Surveillance\nReport": (A, y(3.5)), "Export Data": (A, y(2.7)),
        "Manage Users\nand Rules": (A, y(1.9)), "Manage Backups": (A, y(1.1)),
        "Log In": (B, y(8.35)), "Validate Record": (B, y(7.55)),
        "Compute Thresholds": (B, y(6.7)), "Send Outbreak\nNotification": (B, y(5.9)),
        "Locate Case\nAddresses": (B, y(5.1)), "Write Audit Log": (B, y(2.7)),
        "Restore Backup": (B, y(1.1)),
    }
    for n, (x, yy) in pos.items():
        ax.add_patch(Ellipse((x, yy), WA if x == A else WB, H, fc=FILL, ec=INK, lw=0.8))
        ax.text(x, yy, n, ha="center", va="center", fontsize=7.3, linespacing=1.1)

    def pt(n, side):
        x, yy = pos[n]
        w = WA if x == A else WB
        return {"L": (x - w / 2, yy), "R": (x + w / 2, yy), "T": (x, yy + H / 2),
                "B": (x, yy - H / 2)}[side]

    def rel(src, s_side, dst, d_side, kind, rad=0.0, frac=0.5, dx=0.0, dy=0.06):
        s, d = pt(src, s_side), pt(dst, d_side)
        color = BLUE if kind == "include" else AMBER
        arrow(ax, s, d, dashed=True, color=color, rad=rad, lw=0.75, head=7)
        ax.text(s[0] + (d[0] - s[0]) * frac + dx, s[1] + (d[1] - s[1]) * frac + dy,
                f"«{kind}»", fontsize=6.5, style="italic", ha="center", color=color,
                bbox=dict(fc="white", ec="none", pad=0.2))

    # «include»: base -> included;  «extend»: extension -> base
    rel("Encode Case Record", "R", "Validate Record", "L", "include")
    rel("Import Case Records", "T", "Encode Case Record", "B", "extend", dx=0.3, dy=-0.03)
    rel("Monitor Epidemic\nThresholds", "R", "Compute Thresholds", "L", "include", dy=0.05)
    rel(PR, "T", "Monitor Epidemic\nThresholds", "B", "include", dx=-0.32, dy=-0.03)
    rel(PR, "B", "Detect Hotspots", "T", "include", dx=-0.32, dy=-0.03)
    rel("Send Outbreak\nNotification", "L", "Monitor Epidemic\nThresholds", "R", "extend",
        frac=0.5, dy=0.07)
    rel("Send Outbreak\nNotification", "L", "Detect Hotspots", "R", "extend", frac=0.3,
        dx=-0.12, dy=0.06)
    rel("Detect Hotspots", "R", "Locate Case\nAddresses", "L", "include", dy=0.05)
    rel("Generate Surveillance\nReport", "R", "Write Audit Log", "L", "include", frac=0.55)
    rel("Export Data", "T", "Generate Surveillance\nReport", "B", "extend", dx=-0.3,
        dy=-0.03)
    rel("Export Data", "R", "Write Audit Log", "L", "include", dy=0.05)
    rel("Manage Users\nand Rules", "R", "Write Audit Log", "L", "include", frac=0.55,
        dy=-0.15)
    rel("Restore Backup", "L", "Manage Backups", "R", "extend")

    actors = {"Data Encoder": (0.42, y(7.75)), "Health Analyst": (0.42, y(4.75)),
              "Administrator": (0.42, y(1.55))}
    for name, (x, yy) in actors.items():
        stick(ax, x, yy, name)
    links = {"Data Encoder": ["Encode Case Record", "Import Case Records"],
             "Health Analyst": ["Monitor Epidemic\nThresholds", PR, "Detect Hotspots",
                                "View Trend Forecast", "Generate Surveillance\nReport",
                                "Export Data"],
             "Administrator": ["Export Data", "Manage Users\nand Rules", "Manage Backups"]}
    for name, ucs in links.items():
        x, yy = actors[name]
        for uc in ucs:
            lx, ly = pt(uc, "L")
            ax.plot([x + 0.15, lx], [yy + 0.09, ly], color=INK, lw=0.6)

    for label, target in (("HRMO\nPortal", "Log In"),
                          ("Notification\nGateway", "Send Outbreak\nNotification")):
        _, yy = pos[target]
        ax.add_patch(Rectangle((5.08, yy - 0.3), 0.9, 0.6, fc=SOFT, ec=INK, lw=0.8))
        ax.text(5.53, yy + 0.19, "«system»", ha="center", va="center", fontsize=6.5,
                style="italic")
        ax.text(5.53, yy - 0.06, label, ha="center", va="center", fontsize=7.2,
                fontweight="bold", linespacing=1.05)
        rx, ry = pt(target, "R")
        ax.plot([rx, 5.08], [ry, yy], color=INK, lw=0.6)

    ax.text(4.92, 0.08, "All use cases «include» Log In; every data-changing use case "
            "«include» Write Audit Log", ha="right", va="bottom", fontsize=6.5,
            style="italic", color=BLUE)
    save(fig, "fig03_use_case.png")


# --- Figure 3: Architecture -----------------------------------------------------
def architecture():
    fig, ax = canvas(5.0)
    lx, lw_ = 0.95, 3.75
    layers = [
        ("Presentation Layer", "React single-page application, Leaflet.js maps,\n"
         "Chart.js trend charts, Tailwind CSS dashboard", FILL, 3.45),
        ("Application Logic Layer (Laravel 8, PHP 7.4)", "CESU-only authentication and role "
         "checks, case management,\nrisk tiering, resource recommendation, notification "
         "dispatch,\nreports and export, audit logging", "#ecfdf5", 2.25),
        ("Analytics Service Layer (Python 3.8, FastAPI, localhost)", "threshold computation, "
         "address geocoding,\nDBSCAN hotspot detection, Prophet trend forecasting",
         "#fff7ed", 1.15),
        ("Data Layer (MySQL 8)", "cases, reference tables, thresholds, clusters, "
         "recommendations,\nnotification and audit logs; encrypted backups (AES-256)",
         "#f1f5f9", 0.05),
    ]
    heights = {3.45: 0.85, 2.25: 0.95, 1.15: 0.85, 0.05: 0.85}
    for title, body, fill, y0 in layers:
        h = heights[y0]
        rbox(ax, lx, y0, lw_, h, fill)
        ax.text(lx + lw_ / 2, y0 + h - 0.13, title, ha="center", va="top", fontsize=8,
                fontweight="bold")
        ax.text(lx + lw_ / 2, y0 + (h - 0.25) / 2, body, ha="center", va="center",
                fontsize=7, linespacing=1.3)
    for top, bottom in ((3.45, 3.2), (2.25, 2.0), (1.15, 0.9)):
        arrow(ax, (2.7, top - 0.01), (2.7, bottom + 0.01), lw=1.1, head=9)
        arrow(ax, (3.0, bottom + 0.01), (3.0, top - 0.01), lw=1.1, head=9, color="#64748b")
    rbox(ax, 1.75, 4.55, 2.15, 0.36, "white")
    ax.text(2.82, 4.73, "Authorized CESU user (browser, HTTPS)", ha="center", va="center",
            fontsize=7)
    arrow(ax, (2.82, 4.54), (2.82, 4.31), lw=1.1, head=9)
    externals = [("HRMO Portal\n(authentication)", 2.85, 2.55),
                 ("SMS Gateway and\nEmail Service", 2.05, 2.45),
                 ("Nominatim\nGeocoding", 1.3, 1.5)]
    for text, y0, src_y in externals:
        rbox(ax, 4.88, y0, 1.1, 0.5, SOFT)
        ax.text(5.43, y0 + 0.25, text, ha="center", va="center", fontsize=6.8,
                linespacing=1.15)
        arrow(ax, (lx + lw_ + 0.01, src_y), (4.87, y0 + 0.25), lw=0.8, head=7)
    rbox(ax, 0.0, 0.05, 0.85, 0.85, SOFT)
    ax.text(0.425, 0.475, "Scheduled\njobs and\nencrypted\nbackups", ha="center",
            va="center", fontsize=6.8, linespacing=1.15)
    arrow(ax, (0.86, 0.475), (0.94, 0.475), lw=0.9, head=7)
    save(fig, "fig02_architecture.png")


# --- Figure 4: Outbreak management flow ---------------------------------------
def flow():
    fig, ax = canvas(1.55)
    steps = [("DETECT", "Counts exceed\nthe epidemic\nthreshold", "#dbeafe"),
             ("LOCATE", "DBSCAN finds\nhotspots (200 m,\n3 cases, 4 weeks)", "#e0e7ff"),
             ("PRIORITIZE", "Rule-based\nrisk tier: High,\nModerate, Low", "#fef3c7"),
             ("RECOMMEND", "Medicines,\npersonnel, and\nsupplies by rule", "#dcfce7"),
             ("NOTIFY", "SMS and email\nto designated\npersonnel", "#fee2e2")]
    w, gap = 1.0, 0.25
    for i, (title, body, fill) in enumerate(steps):
        x = i * (w + gap)
        rbox(ax, x + 0.01, 0.05, w - 0.02, 1.45, fill)
        ax.text(x + w / 2, 1.3, title, ha="center", va="center", fontsize=8,
                fontweight="bold")
        ax.text(x + w / 2, 0.62, body, ha="center", va="center", fontsize=7,
                linespacing=1.25)
        if i < len(steps) - 1:
            arrow(ax, (x + w + 0.01, 0.78), (x + w + gap - 0.01, 0.78), lw=1.3, head=9)
    save(fig, "fig04_outbreak_flow.png")


if __name__ == "__main__":
    ipo()
    use_case()
    architecture()
    flow()
