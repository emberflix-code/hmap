"""Builds the panel compliance matrix (comments, actions taken, page references).

Page numbers are read from the rendered manuscript PDF that paginate.py
produces, so run `python paginate.py` first.

Usage: python build_revision_matrix.py
"""
import subprocess
from pathlib import Path

from docx import Document
from docx.enum.section import WD_ORIENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt

HERE = Path(__file__).resolve().parent
PDF = HERE / "Chapters_1to3_Final_Revision.pdf"
OUT = HERE / "Panel_Revision_Matrix.docx"

pages = [[ln.strip() for ln in pg.splitlines()] for pg in subprocess.run(
    ["pdftotext", "-layout", str(PDF), "-"], capture_output=True, text=True,
    encoding="utf-8", errors="replace").stdout.split("\f")]
BODY = next(i for i, p in enumerate(pages) if "Chapter 1" in p)


def pg(heading, prefix=False):
    """Printed page number of the first body page where a heading line appears."""
    for i in range(BODY, len(pages)):
        if any((ln.startswith(heading) if prefix else ln == heading) for ln in pages[i]):
            return str(i - BODY + 1)
    raise LookupError(heading)


def where(*items):
    """'Ch.3, Module 9 (p. 54); ...' from (label, heading, prefix) tuples."""
    return "; ".join(f"{label} (p. {pg(h, pre)})" for label, h, pre in items)


S1 = "Panelist, comment sheet 1"
S2 = "Panelist Dennis, comment sheet 2"
ROWS = [
    # (source, comment, action taken, location)
    (S1, "Since the system handles health-related case data, consider data privacy and "
         "security: role-based access control, audit logs, data encryption (if possible), and "
         "secure backup procedures.",
     "Added Module 9, Security and System Administration: role-based access limited to "
     "authorized CESU personnel, multi-factor authentication for accounts with access to "
     "patient-level records, an append-only audit log, HTTPS, AES-256 encrypted daily "
     "backups with test restorations, and a 72-hour breach response procedure. Supported by "
     "a new literature section on data security and privacy.",
     where(("Ch.3, Module 9", "Module 9:", True),
           ("Ch.3, Security Considerations", "Security Considerations", False),
           ("Ch.2, Data Security and Privacy", "Data Security and Privacy in Health "
            "Information Systems", False))),
    (S1, "Consider adding SMS/email outbreak alerts and notifications.",
     "Added Module 7, Outbreak Alerts and Notifications: SMS and email to designated "
     "personnel on threshold exceedance or a new hotspot, at most one per disease, barangay, "
     "alert type, and week, with no patient identifiers and a delivery log. Supported by a new "
     "literature section on outbreak alerts and notification.",
     where(("Ch.1, Specific Objective 1g", "Specific Objectives:", False),
           ("Ch.3, Module 7", "Module 7:", True),
           ("Ch.2, Outbreak Alerts and Notification", "Outbreak Alerts and Notification",
            False))),
    (S1, "In the scope and limitations, discuss whether the system predicts exact outbreak "
         "occurrence or only probable trends; dependence on the completeness of PIDSR "
         "historical records; prediction accuracy varying with missing or inconsistent "
         "reports; forecasts limited to diseases in the dataset; not intended to replace "
         "physician diagnosis.",
     "Added all five as explicit limitations (a) probable trends only, (b) dependence on "
     "complete and timely PIDSR records and reduced accuracy with missing, delayed, or "
     "inconsistent reports, (d) limited to diseases in the dataset, and (f) not a replacement "
     "for physician diagnosis or epidemiologist judgment, plus limitations on address "
     "accuracy, rule-based recommendations, SMS cost, and evaluation scope.",
     where(("Ch.1, Scope and Limitations", "Scope and Limitations of the Study", False))),
    (S1, "In Chapter 3, add a use case diagram for the proposed system; consider the use of "
         "<<include>> and <<extend>> relations.",
     "Added Use Case Analysis with five actors, a use case diagram using «include» and "
     "«extend» relationships (Figure 2), and a table of use cases, actors, and "
     "relationships (Table 3).",
     where(("Ch.3, Use Case Analysis", "Use Case Analysis", False),
           ("Figure 2", "Figure 2.", True), ("Table 3", "Table 3", False))),
    (S1, "Title revision: Web-Based Disease Outbreak Management System for the City "
         "Epidemiology Surveillance Unit.",
     "Adopted the recommended title throughout: \"Web-Based Disease Outbreak Management "
     "System for the City Epidemiology and Surveillance Unit\" (the unit's official name). "
     "The former short name is no longer used.",
     "Title page (p. i); all chapters"),
    (S1, "Consider alignment to MIT output (CMO 15 s. 2019). Data training, testing, and "
         "validation may not be included. Existing models may be used.",
     "Reframed the study as system development. Cited CMO 15 s. 2019 for the professional "
     "track and capstone, and CMO 07 s. 2010 for the MIT capstone as an output useful in the "
     "development of IT solutions. Removed the Random Forest model and all model training "
     "and validation protocols; Prophet is used as an existing model in its standard "
     "configuration.",
     where(("Ch.1, Introduction", "Introduction", False),
           ("Ch.3, Research Design", "Research Design", False),
           ("Ch.3, Module 5", "Module 5:", True))),
    (S1, "Spatio-temporal analysis may be used also.",
     "Added Module 4, Spatio-Temporal Hotspot Detection, applying the CESU rule of three or "
     "more cases within 200 meters and four weeks with the DBSCAN algorithm, so that "
     "clusters crossing barangay boundaries are visible. Supported by a new literature "
     "section.",
     where(("Ch.3, Module 4", "Module 4:", True),
           ("Ch.2, Spatio-Temporal Hotspot Detection", "Spatio-Temporal Hotspot Detection",
            False))),
    (S1, "A recommender system may be incorporated instead of data training.",
     "Added Module 6, Risk Prioritization and Resource Allocation Recommendation: a "
     "transparent rule-based risk tier and a knowledge-based recommender whose rule table is "
     "encoded from the CESU response protocol and validated with CESU personnel.",
     where(("Ch.3, Module 6", "Module 6:", True),
           ("Ch.2, Decision Support", "Decision Support for Outbreak Response and Resource "
            "Allocation", False))),
    (S1, "Consult the ethics review; consent should be secured.",
     "As advised by the research adviser, and because TUP has no Research Ethics "
     "Committee, the study rests on written informed consent, the authorization of the City "
     "Health Office and the City Mayor, and a signed and notarized Non-Disclosure and Data "
     "Privacy Agreement. An informed consent form was prepared (Appendix A).",
     where(("Ch.3, Ethical Considerations", "Ethical Considerations", False),
           ("Ch.3, Evaluation Instrument", "Evaluation Instrument", False))),
    (S1, "Provide a more extensive gap analysis to show the novelty of the study.",
     "Rewrote Chapter 2 around eleven topical sections with 80 verified references, added a "
     "comparison of related systems (Table 1), a thematic gap analysis with five themes "
     "(Table 2), and a synthesis stating the specific gap.",
     where(("Ch.2, Thematic Gap Analysis", "Thematic Gap Analysis", False),
           ("Table 1", "Table 1", False), ("Table 2", "Table 2", False),
           ("Ch.2, Synthesis", "Synthesis", False))),
    (S1, "The system should be able to determine the hotspot area to trigger resource "
         "allocation like medicines.",
     "Detected hotspots and threshold status determine each barangay's risk tier, which "
     "triggers recommended medicines, personnel, and supplies (Modules 4 and 6), following "
     "the detect, locate, prioritize, recommend, and notify flow.",
     where(("Ch.3, Module 6", "Module 6:", True), ("Figure 4", "Figure 4.", True))),
    (S1, "Consult the CESU regarding validation, or other domain experts regarding the system "
         "output.",
     "Added an output validation questionnaire answered by CESU and City Health Office "
     "personnel on the agreement of alerts, hotspots, report figures, forecasts, and "
     "recommendations with professional judgment, with an acceptance criterion of 3.41.",
     where(("Ch.3, Evaluation Procedure", "Evaluation Procedure", False),
           ("Table 6", "Table 6", False))),
    (S1, "Describe how the system will be tested; identify measurable parameters for testing "
         "validation and use case analysis.",
     "Added a three-level Software Testing Plan with a test case format and a table of "
     "measurable parameters and pass criteria for every module (Table 4), for example "
     "notification within 5 minutes and detection of 100 percent of planted clusters.",
     where(("Ch.3, Software Testing Plan", "Software Testing Plan", False),
           ("Table 4", "Table 4", False))),
    (S2, "Revisit CMO 15 s. 2019 about the research output of the student, such as system "
         "development and system management; change the title based on CMO 15 s. 2019.",
     "Addressed together with the title and MIT-output comments above: new title, study "
     "framed as system development, and CHED policies cited accurately (CMO 15 s. 2019 and "
     "CMO 07 s. 2010).",
     where(("Ch.1, Introduction", "Introduction", False),
           ("Ch.3, Research Design", "Research Design", False))),
    (S2, "In terms of ethical consideration, integrate the data privacy and security standard "
         "in data gathering.",
     "Ethical Considerations now cover protection of patient data (records stay on City "
     "Health Office servers; only anonymized data in any test or demonstration version), "
     "confidentiality of respondents, and the Non-Disclosure and Data Privacy Agreement, "
     "consistent with RA 10173.",
     where(("Ch.3, Ethical Considerations", "Ethical Considerations", False))),
    (S2, "Make the gap analysis comprehensive; why surveillance? Identify the outbreak hotspot.",
     "Chapter 1 now explains surveillance as the information backbone of outbreak "
     "management, citing evidence that most detection and response delays occur at the "
     "municipal level; hotspot identification is Module 4.",
     where(("Ch.1, Introduction", "Introduction", False),
           ("Ch.3, Module 4", "Module 4:", True))),
    (S2, "Make some urgency in terms of providing facilities, workforce, and budgets.",
     "Added an urgency paragraph on CESU staffing, reporting facilities, and budget, and a "
     "literature section on the workforce, budget, and coordination constraints of "
     "Philippine local health units. The CESU figures are to be supplied by the CESU.",
     where(("Ch.1, Background of the Study", "Background of the Study", False),
           ("Ch.2, Resource Constraints", "Resource Constraints of Local Health Units",
            False))),
    (S2, "Researcher ethical consideration: ethics review.",
     "Addressed with the ethics comment above (informed consent, institutional "
     "authorization, and the notarized Non-Disclosure Agreement, as TUP has no Research "
     "Ethics Committee).",
     where(("Ch.3, Ethical Considerations", "Ethical Considerations", False))),
    (S2, "Research gap: use thematic analysis to combine the same insights based on the theme.",
     "Applied thematic analysis following Braun and Clarke (2006); the reviewed literature "
     "is grouped into five themes with the remaining gap for each.",
     where(("Ch.2, Thematic Gap Analysis", "Thematic Gap Analysis", False),
           ("Table 2", "Table 2", False))),
    (S2, "Validation of results and instrument from the CESU; user acceptance.",
     "The system is evaluated for acceptability with an ISO/IEC 25010:2023-based instrument "
     "and its outputs are validated by CESU personnel; the instrument and consent form are "
     "prepared for administration.",
     where(("Ch.3, Evaluation Instrument", "Evaluation Instrument", False),
           ("Ch.3, Evaluation Procedure", "Evaluation Procedure", False))),
]

doc = Document()
sec = doc.sections[0]
sec.orientation = WD_ORIENT.LANDSCAPE
sec.page_width, sec.page_height = Inches(11), Inches(8.5)
for m in ("top_margin", "bottom_margin", "right_margin"):
    setattr(sec, m, Inches(0.8))
sec.left_margin = Inches(1.0)
style = doc.styles["Normal"]
style.font.name = "Times New Roman"
style.font.size = Pt(10.5)


def line(text, size=12, bold=False, italic=False, after=2):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after = Pt(after)
    r = p.add_run(text)
    r.bold, r.italic = bold, italic
    r.font.size = Pt(size)


line("PANEL RECOMMENDATIONS AND ACTIONS TAKEN", 13, bold=True)
line("Web-Based Disease Outbreak Management System for the City Epidemiology and "
     "Surveillance Unit", 11, italic=True)
line("Kemberly M. Magsino, Master in Information Technology, Technological University of the "
     "Philippines Manila", 10.5, after=10)

widths = [Inches(1.2), Inches(2.6), Inches(3.6), Inches(1.8)]
table = doc.add_table(rows=1, cols=4)
table.style = "Table Grid"
table.autofit = False
for cell, text, w in zip(table.rows[0].cells,
                         ["Source", "Comment or Suggestion", "Action Taken", "Location"],
                         widths):
    cell.width = w
    run = cell.paragraphs[0].add_run(text)
    run.bold = True
    cell.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:fill"), "D9D9D9")
    cell._tc.get_or_add_tcPr().append(shd)
hdr = table.rows[0]._tr.get_or_add_trPr()
rep = OxmlElement("w:tblHeader")
hdr.append(rep)  # repeat the header row on every page
for source, comment, action, loc in ROWS:
    cells = table.add_row().cells
    for cell, text, w in zip(cells, (source, comment, action, loc), widths):
        cell.width = w
        cell.paragraphs[0].add_run(text)
    cant = OxmlElement("w:cantSplit")
    table.rows[-1]._tr.get_or_add_trPr().append(cant)

p = doc.add_paragraph()
p.paragraph_format.space_before = Pt(8)
r = p.add_run("Page numbers refer to the revised Chapters 1 to 3 manuscript. Comments are "
              "transcribed from the handwritten proposal defense comment sheets (Form "
              "F-COS-3.5-TPD).")
r.italic = True
r.font.size = Pt(9.5)

doc.save(OUT)
print("saved", OUT, "rows:", len(ROWS))
