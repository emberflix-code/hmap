"""Builds the CESU validation sheet for the draft recommendation rules (Ch.3 Module 6).

Usage: python build_rule_validation_sheet.py <out.docx>

The rules are read from ml/migrations/2026_10_30_recommendations.sql, so the
sheet always lists exactly what the system was seeded with. Rule numbers
(R01, R02, ...) follow the order of the migration, which is also the rule_id
order on a database seeded with the full disease list.
"""
import os
import re
import sys
from docx import Document
from docx.enum.section import WD_ORIENT
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

OUT = sys.argv[1]
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..", "..")
LOGOS = os.path.join(HERE, "..", "Final Defense Revision", "letterhead")
MIGRATION = os.path.join(ROOT, "ml", "migrations", "2026_10_30_recommendations.sql")
TITLE = ("Web-Based Disease Outbreak Management System for the City "
         "Epidemiology and Surveillance Unit")
J, C, L = WD_ALIGN_PARAGRAPH.JUSTIFY, WD_ALIGN_PARAGRAPH.CENTER, WD_ALIGN_PARAGRAPH.LEFT

DISEASE_NAMES = {
    "DENGUE": "Dengue", "MEA": "Measles", "AFP": "Acute Flaccid Paralysis",
    "LEP": "Leptospirosis", "TYP": "Typhoid Fever", "HFMD": "Hand, Foot and Mouth Disease",
    "ILI": "Influenza-Like Illness", None: "Any other disease (no rules of its own)",
}
CATEGORY = {"Team": "Team", "Supply": "Supply", "Medicine": "Medicine", "IEC": "Information material"}


def parse_rules(path):
    """[(disease_code or None, tier, category, item, basis, factor, unit, source, notes)] in file order."""
    sql = open(path, encoding="utf-8").read()
    rules = []
    pattern = re.compile(
        r"INSERT INTO recommendation_rules \([^)]*\)\s*"
        r"(?:SELECT disease_id,|VALUES \(NULL,)\s*(.*?)\s*"
        r"(?:FROM diseases WHERE disease_code = '([A-Z]+)'|\))\s*;", re.S)
    literal = re.compile(r"'([^']*)'|(NULL)|([0-9.]+)")
    for values, code in pattern.findall(sql):
        vals = []
        for s, null, num in literal.findall(values):
            vals.append(s if s or (not null and not num) else (None if null else float(num)))
        tier, category, item, basis, factor, unit, _priority, source, notes = vals
        rules.append((code or None, tier, category, item, basis, factor, unit, source, notes))
    return rules


def quantity_text(basis, factor, unit):
    if basis == "as_assessed":
        return "As assessed by CESU"
    n = f"{factor:g}" if factor is not None else "?"
    if factor == 1 and unit and unit.endswith("s"):
        unit = unit[:-1]   # "1 kit per active case", not "1 kits"
    if basis == "fixed":
        return f"{n} {unit or ''}".strip()
    if basis == "per_case":
        return f"{n} {unit or ''} per active case".replace("  ", " ")
    return f"{n} {unit or ''} per 1,000 residents".replace("  ", " ")


doc = Document()
sec = doc.sections[0]
sec.orientation = WD_ORIENT.LANDSCAPE
sec.page_width, sec.page_height = Inches(11.69), Inches(8.27)
sec.top_margin, sec.bottom_margin = Inches(1.35), Inches(0.7)
sec.left_margin = sec.right_margin = Inches(0.8)
sec.header_distance = Inches(0.3)
TEXT_W = 11.69 - 1.6
normal = doc.styles["Normal"]
normal.font.name = "Times New Roman"
normal.font.size = Pt(11)
normal.paragraph_format.space_after = Pt(0)


def para(text="", bold=False, italic=False, align=None, after=4, size=None, before=0):
    p = doc.add_paragraph()
    if text:
        r = p.add_run(text)
        r.bold, r.italic = bold, italic
        if size:
            r.font.size = Pt(size)
    if align is not None:
        p.alignment = align
    p.paragraph_format.space_after = Pt(after)
    p.paragraph_format.space_before = Pt(before)
    return p


def fixed_table(rows, widths):
    t = doc.add_table(rows=rows, cols=len(widths))
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = False
    layout = OxmlElement("w:tblLayout")
    layout.set(qn("w:type"), "fixed")
    t._tbl.tblPr.append(layout)
    t.style = "Table Grid"
    for col, w in zip(t.columns, widths):
        col.width = Inches(w)
    for row in t.rows:
        for cell, w in zip(row.cells, widths):
            cell.width = Inches(w)
    return t


def cell_text(cell, text, bold=False, align=None, size=9.5, italic=False):
    p = cell.paragraphs[0]
    r = p.add_run(text)
    r.bold, r.italic = bold, italic
    r.font.size = Pt(size)
    if align is not None:
        p.alignment = align


def shade(cell, hex_fill):
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), hex_fill)
    tc_pr.append(shd)


def repeat_header(row):
    tr_pr = row._tr.get_or_add_trPr()
    el = OxmlElement("w:tblHeader")
    el.set(qn("w:val"), "true")
    tr_pr.append(el)


def no_split(row):
    tr_pr = row._tr.get_or_add_trPr()
    tr_pr.append(OxmlElement("w:cantSplit"))


# --- letterhead (same as the evaluation instrument) -------------------------
header = sec.header
ht = header.add_table(rows=1, cols=3, width=Inches(6.27))
ht.alignment = WD_TABLE_ALIGNMENT.CENTER
ht.autofit = False
lay = OxmlElement("w:tblLayout")
lay.set(qn("w:type"), "fixed")
ht._tbl.tblPr.append(lay)
for col, w in zip(ht.columns, (0.85, 4.67, 0.75)):
    col.width = Inches(w)
for cell, w in zip(ht.rows[0].cells, (0.85, 4.67, 0.75)):
    cell.width = Inches(w)
left, mid, right = ht.rows[0].cells
left.paragraphs[0].add_run().add_picture(os.path.join(LOGOS, "tup_logo.png"), width=Inches(0.8))
right.paragraphs[0].add_run().add_picture(os.path.join(LOGOS, "tuv_logo.png"), width=Inches(0.7))
right.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.RIGHT
for i, (text, size) in enumerate([
        ("TECHNOLOGICAL UNIVERSITY OF THE PHILIPPINES", 15),
        ("Ayala Blvd., Ermita, Manila, 1000, Philippines", 9.5),
        ("Tel. No. +632-301-3001 | Fax No. +632-521-4063", 9.5),
        ("Email: tup@tup.edu.ph | Website: www.tup.edu.ph", 9.5)]):
    q = mid.paragraphs[0] if i == 0 else mid.add_paragraph()
    q.alignment = C
    q.paragraph_format.space_after = Pt(4 if i == 0 else 0)
    r = q.add_run(text)
    r.font.name = "Calibri"
    r._element.rPr.rFonts.set(qn("w:eastAsia"), "Calibri")
    r.font.size = Pt(size)
    r.font.color.rgb = RGBColor(0x33, 0x33, 0x33)
mid.paragraphs[0].paragraph_format.space_before = Pt(6)
header.paragraphs[0]._element.getparent().remove(header.paragraphs[0]._element)

# --- title and instructions -------------------------------------------------
para("College of Science  |  Master in Information Technology", align=C, after=6, size=10.5)
para("VALIDATION OF RESPONSE RECOMMENDATION RULES", bold=True, align=C, after=2, size=13)
para(TITLE, italic=True, align=C, after=10)

para("Purpose. When a barangay is rated Moderate or High risk for a disease, the system lists "
     "the response teams, supplies, medicines, and information materials to deploy there. "
     "These lists come from the rules below. The rules were drafted by the researcher from "
     "published guidance: the PIDSR Manual of Procedures (DOH, 2014), the DOH 4S strategy "
     "against dengue, the WHO dengue guidelines (2009), and WHO standards for measles and "
     "acute flaccid paralysis. Rules marked “CESU to confirm” have no published "
     "source and depend on CESU practice. Until CESU validates a rule, the system shows the "
     "recommendations based on it as drafts.", align=J, after=6)
para("How the rules apply.", bold=True, after=2)
for text in [
        "Moderate risk: the barangay is above its epidemic threshold, has an active dengue "
        "hotspot, or shows a rising forecast. A single case of measles or acute flaccid "
        "paralysis is enough.",
        "High risk: the barangay is above its epidemic threshold and also has an active hotspot.",
        "Rules for Moderate apply to both Moderate and High barangays. Rules for High are "
        "added only for High barangays.",
        "An active case is a Confirmed or Probable case in the barangay in the last four "
        "morbidity weeks. “As assessed by CESU” means the system names the item but "
        "leaves the quantity to CESU."]:
    p = para("•  " + text, align=J, after=2)
    p.paragraph_format.left_indent = Inches(0.25)
para("Instructions. For each rule, tick one box. Agree keeps the rule as written. Revise "
     "means the rule is kept with the change you write in the last column, for example a "
     "different item, quantity, or unit. Remove deletes the rule. Please also list any "
     "response CESU usually takes that is missing, in the table at the end.", align=J,
     before=4, after=8)

# --- rule table -------------------------------------------------------------
rules = parse_rules(MIGRATION)
widths = [0.45, 0.8, 0.85, 2.2, 1.0, 1.4, 0.68, 0.68, 0.68, 0.0]
widths[-1] = round(TEXT_W - sum(widths[:-1]), 2)
heads = ["No.", "Risk tier", "Type", "Recommended response", "Quantity", "Source",
         "Agree", "Revise", "Remove", "Revision or comment"]

t = fixed_table(1, widths)
for cell, h in zip(t.rows[0].cells, heads):
    cell_text(cell, h, bold=True, align=C, size=9.5)
    shade(cell, "D9D9D9")
repeat_header(t.rows[0])

current = object()
for n, (code, tier, category, item, basis, factor, unit, source, notes) in enumerate(rules, 1):
    if code != current:
        current = code
        row = t.add_row()
        no_split(row)
        merged = row.cells[0].merge(row.cells[-1])
        cell_text(merged, DISEASE_NAMES.get(code, code), bold=True, size=10)
        merged.paragraphs[0].paragraph_format.keep_with_next = True   # stay with its first rule
        shade(merged, "F2F2F2")
    row = t.add_row()
    no_split(row)
    c = row.cells
    cell_text(c[0], f"R{n:02d}", align=C)
    cell_text(c[1], tier, align=C)
    cell_text(c[2], CATEGORY[category])
    cell_text(c[3], item)
    if notes:
        q = c[3].add_paragraph()
        r = q.add_run(notes)
        r.italic = True
        r.font.size = Pt(8.5)
    cell_text(c[4], quantity_text(basis, factor, unit))
    cell_text(c[5], source, size=8.5)
    for k in (6, 7, 8):
        cell_text(c[k], "☐", align=C, size=12)

# --- missing responses --------------------------------------------------------
para("", after=6)
p = para("Responses CESU usually takes that are missing above", bold=True, after=4)
p.paragraph_format.keep_with_next = True
w2 = [1.9, 0.9, 1.1, 3.2, TEXT_W - 1.9 - 0.9 - 1.1 - 3.2]
t2 = fixed_table(1, w2)
for cell, h in zip(t2.rows[0].cells, ["Disease", "Risk tier", "Type", "Recommended response", "Quantity and basis"]):
    cell_text(cell, h, bold=True, align=C, size=9.5)
    shade(cell, "D9D9D9")
repeat_header(t2.rows[0])
for _ in range(5):
    row = t2.add_row()
    row.height = Inches(0.38)
    no_split(row)

# --- sign-off ---------------------------------------------------------------
para("", after=8)
p = para("Validated by", bold=True, after=6)
p.paragraph_format.keep_with_next = True
w3 = [3.0, 2.6, 2.0, TEXT_W - 7.6]
t3 = fixed_table(1, w3)
for cell, h in zip(t3.rows[0].cells, ["Name", "Position", "Signature", "Date"]):
    cell_text(cell, h, bold=True, align=C, size=9.5)
    shade(cell, "D9D9D9")
for _ in range(3):
    row = t3.add_row()
    row.height = Inches(0.42)
    no_split(row)
para("After validation, the system Administrator records the agreed changes in the rule "
     "table and marks each agreed rule as Validated. Each of these changes is recorded "
     "in the system's audit log.", italic=True, size=9.5, before=8, align=J)

doc.save(OUT)
print(f"saved {OUT}: {len(rules)} rules")
