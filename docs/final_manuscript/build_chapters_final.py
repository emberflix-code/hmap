"""Build Chapters_1to3_Final_Revision.docx after the proposal defense panel's revisions.

Title: Web-Based Disease Outbreak Management System for the City Epidemiology
and Surveillance Unit (no short name in the manuscript). Nine modules, existing
methods only (PIDSR thresholds, DBSCAN, Prophet), rule-based risk tier and
resource recommender, SMS/email notifications, security and backups.
Every citation was re-verified in docs/final_manuscript/research/.
Stack matches the LGU server: PHP 7.4 + Laravel 8, Python 3.8 + FastAPI, MySQL 8.
Figures come from generate_final_figures.py; check_citations.py cross-checks
in-text citations against the reference list.
"""

from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING, WD_TAB_ALIGNMENT
from docx.enum.section import WD_SECTION
from docx.oxml.ns import qn
from docx.oxml import OxmlElement


def add_page_number_field(paragraph):
    """Insert a Word PAGE field at the end of a paragraph (renders to the
    current page number when Word opens the document). APA 7 §2.18 puts page
    numbers in the top-right header on every page."""
    run = paragraph.add_run()
    # Field begin
    fld_begin = OxmlElement("w:fldChar")
    fld_begin.set(qn("w:fldCharType"), "begin")
    run._r.append(fld_begin)
    # Field instruction
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = "PAGE"
    run._r.append(instr)
    # Field end
    fld_end = OxmlElement("w:fldChar")
    fld_end.set(qn("w:fldCharType"), "end")
    run._r.append(fld_end)
    # Style the run
    rPr = OxmlElement("w:rPr")
    rFonts = OxmlElement("w:rFonts")
    rFonts.set(qn("w:ascii"), "Times New Roman")
    rFonts.set(qn("w:hAnsi"), "Times New Roman")
    rPr.append(rFonts)
    sz = OxmlElement("w:sz")
    sz.set(qn("w:val"), "24")  # 12pt (half-points)
    rPr.append(sz)
    run._r.insert(0, rPr)


OUT_PATH = r"C:\xampp\htdocs\hmap\docs\final_manuscript\Chapters_1to3_Final_Revision.docx"
TEXT_WIDTH = 6.0  # inches: US Letter minus the 1.5-inch left and 1-inch right margins
FIG_DIR = r"C:\xampp\htdocs\hmap\docs\final_manuscript\figures"


def set_double_spacing(par):
    par.paragraph_format.line_spacing_rule = WD_LINE_SPACING.DOUBLE


def add_para(doc, text, bold=False, italic=False, size=12, align=WD_ALIGN_PARAGRAPH.JUSTIFY,
             first_line_indent=0.5, space_after=0):
    p = doc.add_paragraph()
    p.alignment = align
    p.paragraph_format.first_line_indent = Inches(first_line_indent)
    p.paragraph_format.space_after = Pt(space_after)
    set_double_spacing(p)
    run = p.add_run(text)
    run.bold = bold
    run.italic = italic
    run.font.name = "Times New Roman"
    run.font.size = Pt(size)
    return p


def add_heading(doc, text, level=1, align=WD_ALIGN_PARAGRAPH.CENTER):
    """APA 7th edition heading. No extra space before/after — double line spacing
    provides the visual gap, and APA explicitly requires zero space_before/after."""
    p = doc.add_paragraph()
    p.alignment = align
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(0)
    p.paragraph_format.keep_with_next = True  # never strand a heading at a page end
    set_double_spacing(p)
    run = p.add_run(text)
    run.bold = True
    run.font.name = "Times New Roman"
    sizes = {1: 14, 2: 13, 3: 12}
    run.font.size = Pt(sizes.get(level, 12))
    return p


def add_section(doc, label, title):
    """Section heading per the submitted PDF format (HMAP_Chapters_1to3_Final.pdf):
    bold-only, no letter or number prefix, left-aligned (subsections) or
    centered (Chapter top-level). 12pt Times New Roman bold, double-spaced,
    zero paragraph spacing. The `label` argument is IGNORED — kept in the
    signature for backward compatibility but dropped from the rendered text
    to match the panel-approved heading style."""
    _ = label  # intentionally unused
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(0)
    p.paragraph_format.first_line_indent = Inches(0)
    p.paragraph_format.keep_with_next = True  # never strand a heading at a page end
    set_double_spacing(p)
    r = p.add_run(title)
    r.bold = True
    r.font.name = "Times New Roman"
    r.font.size = Pt(12)
    return p


def add_chapter_break(doc, label, title, *, page_break=True):
    """APA 7 + Gerios template: new page, then 'Chapter N' / TITLE centered.
    No extra paragraph-level spacing; double line spacing handles the gap.

    page_break=False suppresses the page break, used when a section break has
    already paginated (e.g. Chapter 1 which starts a new section)."""
    if page_break:
        doc.add_page_break()
    p1 = doc.add_paragraph()
    p1.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p1.paragraph_format.space_before = Pt(0)
    p1.paragraph_format.space_after = Pt(0)
    set_double_spacing(p1)
    r1 = p1.add_run(label)
    r1.bold = True
    r1.font.name = "Times New Roman"
    r1.font.size = Pt(12)
    p2 = doc.add_paragraph()
    p2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p2.paragraph_format.space_before = Pt(0)
    p2.paragraph_format.space_after = Pt(0)
    set_double_spacing(p2)
    r2 = p2.add_run(title)
    r2.bold = True
    r2.font.name = "Times New Roman"
    r2.font.size = Pt(12)


def add_bullet(doc, text, level=0):
    p = doc.add_paragraph(style="List Bullet")
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    # APA 7 §2.21: no extra paragraph spacing — line spacing alone separates lines
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(0)
    p.paragraph_format.left_indent = Inches(0.5 + 0.25 * level)
    set_double_spacing(p)
    run = p.add_run(text)
    run.font.name = "Times New Roman"
    run.font.size = Pt(12)
    return p


def add_lettered(doc, letter, text):
    """Lettered list item rendered as a separate paragraph with 'a.', 'b.',
    'c.' style prefix. Per the panel-approved template (Philippine thesis
    convention), unordered enumerations are rendered as lettered paragraphs
    rather than bullet symbols. For ordered sequences where the step number
    is semantically meaningful (e.g., Operational Flow), use add_numbered()
    instead.

    `letter` is a single character ('a', 'b', ...) and is rendered followed
    by a period, in bold, as the paragraph prefix.
    """
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    # APA 7 §2.21: no extra paragraph spacing
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(0)
    p.paragraph_format.left_indent = Inches(0.5)
    p.paragraph_format.first_line_indent = Inches(-0.25)
    set_double_spacing(p)
    r1 = p.add_run(f"{letter}. ")
    r1.bold = True
    r1.font.name = "Times New Roman"
    r1.font.size = Pt(12)
    r2 = p.add_run(text)
    r2.font.name = "Times New Roman"
    r2.font.size = Pt(12)
    return p


def add_numbered(doc, num, text):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    # APA 7 §2.21: no extra paragraph spacing
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(0)
    p.paragraph_format.left_indent = Inches(0.5)
    p.paragraph_format.first_line_indent = Inches(-0.25)
    set_double_spacing(p)
    r1 = p.add_run(f"{num}. ")
    r1.bold = True
    r1.font.name = "Times New Roman"
    r1.font.size = Pt(12)
    r2 = p.add_run(text)
    r2.font.name = "Times New Roman"
    r2.font.size = Pt(12)
    return p


def add_sublettered(doc, letter, text):
    """Lettered list item nested UNDER a numbered parent item, rendered at
    one additional indent level (0.75 inch left indent) so the visual
    hierarchy reads as:

        1.  Numbered parent point
            a.  Sublettered child
            b.  Sublettered child

    Use this helper when the lettered items belong to a numbered parent
    (e.g., Specific Objective 1 with sub-points a-e). For top-level lettered
    enumerations with no numbered parent (e.g., IPO Input items, Security
    Considerations), continue to use add_lettered() at the standard
    0.5-inch indent.
    """
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    # APA 7 §2.21: no extra paragraph spacing
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(0)
    # Nested one level deeper than add_lettered (0.5") and add_numbered (0.5")
    p.paragraph_format.left_indent = Inches(0.75)
    p.paragraph_format.first_line_indent = Inches(-0.25)
    set_double_spacing(p)
    r1 = p.add_run(f"{letter}. ")
    r1.bold = True
    r1.font.name = "Times New Roman"
    r1.font.size = Pt(12)
    r2 = p.add_run(text)
    r2.font.name = "Times New Roman"
    r2.font.size = Pt(12)
    return p


def add_blank(doc, n=1):
    for _ in range(n):
        doc.add_paragraph()


def add_figure(doc, image_path, caption, width_inches=5.5, note=None):
    """Figure with caption BELOW the image, matching the submitted PDF format:

        [image, centered]
        Figure N. Short Title                  (bold, centered, 12pt)
        Note. One-sentence clarification.      (italic, centered, 11pt, optional)

    `caption` should be the short bold caption, e.g.:
        'Figure 1. Conceptual Model of the Study'

    `note` is an optional one-sentence italicized note shown below the caption,
    used only when a brief clarification adds value beyond the title. Pass
    None (default) to omit the note line entirely.
    """
    # Image centered
    img_par = doc.add_paragraph()
    img_par.alignment = WD_ALIGN_PARAGRAPH.CENTER
    img_par.paragraph_format.space_before = Pt(0)
    img_par.paragraph_format.space_after = Pt(0)
    set_double_spacing(img_par)
    run = img_par.add_run()
    run.add_picture(image_path, width=Inches(min(width_inches, TEXT_WIDTH)))

    # Bold caption centered, below the image
    cap_par = doc.add_paragraph()
    cap_par.alignment = WD_ALIGN_PARAGRAPH.CENTER
    cap_par.paragraph_format.space_before = Pt(0)
    cap_par.paragraph_format.space_after = Pt(0)
    set_double_spacing(cap_par)
    # TUP format: italic "Figure N." label followed by a bold title
    label, _, title = caption.partition(". ")
    rl = cap_par.add_run(label + ". ")
    rl.italic = True
    rl.font.name = "Times New Roman"
    rl.font.size = Pt(12)
    rc = cap_par.add_run(title)
    rc.bold = True
    rc.font.name = "Times New Roman"
    rc.font.size = Pt(12)

    # Optional one-sentence italic note centered below the caption
    if note:
        note_par = doc.add_paragraph()
        note_par.alignment = WD_ALIGN_PARAGRAPH.CENTER
        note_par.paragraph_format.space_before = Pt(0)
        note_par.paragraph_format.space_after = Pt(0)
        set_double_spacing(note_par)
        rn1 = note_par.add_run("Note. ")
        rn1.italic = True
        rn1.font.name = "Times New Roman"
        rn1.font.size = Pt(11)
        rn2 = note_par.add_run(note)
        rn2.italic = True
        rn2.font.name = "Times New Roman"
        rn2.font.size = Pt(11)

    return img_par


def add_table(doc, number, title, headers, rows, widths, font_size=10):
    """APA 7 table: bold 'Table N' line, italic title line, then a grid table.
    `widths` are column widths in inches. The first column is left-aligned;
    in other columns, short cells (two words or fewer) are centered. The
    heading and all rows are kept on one page where the table fits."""
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(6)
    p.paragraph_format.space_after = Pt(0)
    p.paragraph_format.keep_with_next = True
    r = p.add_run(f"Table {number}")
    r.bold = True
    r.font.name = "Times New Roman"
    r.font.size = Pt(12)
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(6)
    p.paragraph_format.keep_with_next = True
    r = p.add_run(title)
    r.italic = True
    r.font.name = "Times New Roman"
    r.font.size = Pt(12)
    total = sum(widths)
    if total > TEXT_WIDTH:  # scale proportionally to fit the text block
        widths = [w * TEXT_WIDTH / total for w in widths]
    table = doc.add_table(rows=len(rows) + 1, cols=len(headers))
    table.style = "Table Grid"
    table.autofit = False
    for row in table.rows:
        for cell, w in zip(row.cells, widths):
            cell.width = Inches(w)
    for cell, h in zip(table.rows[0].cells, headers):
        cp = cell.paragraphs[0]
        cp.alignment = WD_ALIGN_PARAGRAPH.CENTER
        cr = cp.add_run(h)
        cr.bold = True
        cr.font.name = "Times New Roman"
        cr.font.size = Pt(font_size)
    for row, vals in zip(table.rows[1:], rows):
        for col, (cell, val) in enumerate(zip(row.cells, vals)):
            cp = cell.paragraphs[0]
            if col > 0 and len(str(val).split()) <= 2:
                cp.alignment = WD_ALIGN_PARAGRAPH.CENTER
            cr = cp.add_run(str(val))
            cr.font.name = "Times New Roman"
            cr.font.size = Pt(font_size)
    for row in table.rows:
        tr_pr = row._tr.get_or_add_trPr()
        cant_split = OxmlElement("w:cantSplit")
        tr_pr.append(cant_split)
        if row is not table.rows[-1]:
            for cell in row.cells:
                for cp in cell.paragraphs:
                    cp.paragraph_format.keep_with_next = True
    doc.add_paragraph()
    return table


# ---------------------------------------------------------------------------
# Build document
# ---------------------------------------------------------------------------
doc = Document()

# Core properties — replace python-docx default author with the actual researcher
doc.core_properties.author = "Kemberly M. Magsino"
doc.core_properties.last_modified_by = "Kemberly M. Magsino"
doc.core_properties.title = (
    "Web-Based Disease Outbreak Management System for the City "
    "Epidemiology and Surveillance Unit"
)

# Default style
style = doc.styles["Normal"]
style.font.name = "Times New Roman"
style.font.size = Pt(12)

# Page size and margins follow the TUP College of Science format reference
# (docs/final_manuscript/Format Reference): US Letter, 1.5-inch left binding
# margin, 1 inch elsewhere, leaving a 6.0-inch text block (TEXT_WIDTH). Line
# spacing is double throughout, enforced per-paragraph by set_double_spacing();
# the 0.5-inch first-line indent is enforced by add_para().
section = doc.sections[0]
section.page_width = Inches(8.5)
section.page_height = Inches(11)
section.top_margin = Inches(1)
section.bottom_margin = Inches(1)
section.left_margin = Inches(1.5)
section.right_margin = Inches(1)

# =================================================================
#                     PRELIMINARIES
# =================================================================
# Title page, Table of Contents, List of Tables, and List of Figures, numbered
# in lower-case Roman numerals (TUP format reference). Page numbers come from
# page_map.json, which paginate.py writes after rendering the document in
# Word; on a first build without the map, the numbers are left blank.
import json
import os

PAGE_MAP_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "page_map.json")
PAGE_MAP = {}
if os.path.exists(PAGE_MAP_PATH):
    with open(PAGE_MAP_PATH, encoding="utf-8") as fh:
        PAGE_MAP = json.load(fh)

# (text, kind): kind "chapter" = unnumbered chapter row, "section" = main heading
TOC_ENTRIES = [
    ("Title Page", "prelim"), ("Table of Contents", "prelim"), ("List of Tables", "prelim"),
    ("List of Figures", "prelim"),
    ("CHAPTER 1 – THE PROBLEM AND ITS BACKGROUND", "chapter"),
    ("Introduction", "section"), ("Background of the Study", "section"),
    ("Objectives of the Study", "section"), ("Significance of the Study", "section"),
    ("Scope and Limitations of the Study", "section"),
    ("CHAPTER 2 – CONCEPTUAL FRAMEWORK", "chapter"),
    ("Review of Related Studies and Literature", "section"), ("Foreign Studies", "section"),
    ("Local Studies", "section"), ("Foreign Systems", "section"), ("Local Systems", "section"),
    ("Thematic Gap Analysis", "section"), ("Synthesis", "section"),
    ("Conceptual Framework", "section"), ("Operational Definition of Terms", "section"),
    ("CHAPTER 3 – METHODOLOGY", "chapter"),
    ("Research Design", "section"), ("Research Project Development", "section"),
    ("Instruments and Techniques Used", "section"),
    ("Data Processing and Statistical Treatment of Data", "section"),
    ("Schedule of Activities", "section"),
    ("REFERENCES", "section"),
]
LIST_OF_TABLES = [
    (1, "Comparison of Related Systems with the Developed System"),
    (2, "Themes Identified in the Reviewed Literature and Remaining Gaps"),
    (3, "Use Cases, Actors, and Relationships"),
    (4, "Measurable Testing Parameters and Pass Criteria"),
    (5, "Five-Point Acceptability Scale and Interpretation"),
    (6, "Five-Point Agreement Scale for Output Validation"),
    (7, "Schedule of Activities"),
]
LIST_OF_FIGURES = [
    (1, "Conceptual Model of the Study"),
    (2, "Use Case Diagram of the System"),
    (3, "System Architecture"),
    (4, "Outbreak Management Flow of the System"),
]


def set_page_numbering(sect, fmt):
    """Restart numbering at 1 in the given format ('lowerRoman' or 'decimal')."""
    pg = OxmlElement("w:pgNumType")
    pg.set(qn("w:fmt"), fmt)
    pg.set(qn("w:start"), "1")
    sect._sectPr.append(pg)


def prelim_line(text, size=12, bold=False, after=0, align=WD_ALIGN_PARAGRAPH.CENTER):
    p = doc.add_paragraph()
    p.alignment = align
    p.paragraph_format.space_after = Pt(after)
    r = p.add_run(text)
    r.bold = bold
    r.font.name = "Times New Roman"
    r.font.size = Pt(size)
    return p


def prelim_heading(text):
    p = prelim_line(text, bold=True, after=18)
    p.paragraph_format.page_break_before = True
    return p


def listing_row(left, page, indent=0.0, bold=False, number=None):
    """One TOC or list row: optional number column, title, right-aligned page."""
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(10)
    p.paragraph_format.left_indent = Inches(indent + (0.6 if number is not None else 0))
    if number is not None:
        p.paragraph_format.first_line_indent = Inches(-0.6)
    p.paragraph_format.tab_stops.add_tab_stop(Inches(TEXT_WIDTH), WD_TAB_ALIGNMENT.RIGHT)
    text = (f"{number}\t" if number is not None else "") + left + (f"\t{page}" if page else "")
    if number is not None:
        p.paragraph_format.tab_stops.add_tab_stop(Inches(indent + 0.6))
    r = p.add_run(text)
    r.bold = bold
    r.font.name = "Times New Roman"
    r.font.size = Pt(12)
    return p


prelim_section = doc.sections[0]
set_page_numbering(prelim_section, "lowerRoman")
prelim_section.different_first_page_header_footer = True  # no number on the title page
prelim_header = prelim_section.header.paragraphs[0]
prelim_header.alignment = WD_ALIGN_PARAGRAPH.RIGHT
add_page_number_field(prelim_header)

# --- Title page (format of docs/final_manuscript/Format Reference/Title Page.pdf)
for _ in range(2):
    prelim_line("")
prelim_line("WEB-BASED DISEASE OUTBREAK MANAGEMENT SYSTEM", bold=True, after=12)
prelim_line("FOR THE CITY EPIDEMIOLOGY AND SURVEILLANCE UNIT", bold=True, after=84)
for text in ("A Capstone", "Presented to the", "Graduate Faculty of the College of Science",
             "Technological University of the Philippines", "Manila"):
    prelim_line(text, after=2)
prelim_line("", after=84)
for text in ("In Partial Fulfilment", "of the Requirements for the Degree",
             "Master in Information Technology"):
    prelim_line(text, after=2)
prelim_line("", after=96)
prelim_line("KEMBERLY M. MAGSINO", after=18)
prelim_line("October 2026")

# --- Table of Contents
prelim_heading("TABLE OF CONTENTS")
listing_row("", "Page", bold=True)
for text, kind in TOC_ENTRIES:
    if kind == "chapter":
        p = listing_row(text, "", bold=True)
        p.paragraph_format.space_before = Pt(6)
    else:
        listing_row(text, PAGE_MAP.get(text, ""))

# --- List of Tables
prelim_heading("LIST OF TABLES")
listing_row("Title", "Page", bold=True, number="Table")
for num, title in LIST_OF_TABLES:
    listing_row(title, PAGE_MAP.get(f"Table {num}", ""), number=num)

# --- List of Figures
prelim_heading("LIST OF FIGURES")
listing_row("Title", "Page", bold=True, number="Figure")
for num, title in LIST_OF_FIGURES:
    listing_row(title, PAGE_MAP.get(f"Figure {num}", ""), number=num)

# =================================================================
#                     CHAPTER 1
# =================================================================
# The chapters start a new section whose Arabic page numbers restart at 1.
body_section = doc.add_section(WD_SECTION.NEW_PAGE)
body_section.different_first_page_header_footer = False
body_section.header.is_linked_to_previous = False
header_par = body_section.header.paragraphs[0]
for run in list(header_par.runs):
    run._element.getparent().remove(run._element)
header_par.alignment = WD_ALIGN_PARAGRAPH.RIGHT
add_page_number_field(header_par)
set_page_numbering(body_section, "decimal")

add_chapter_break(doc, "Chapter 1", "THE PROBLEM AND ITS BACKGROUND",
                  page_break=False)

add_section(doc, "", "Introduction")

add_para(doc, "Public health surveillance is defined as the ongoing, systematic collection, analysis, "
         "interpretation, and dissemination of health data essential for planning, implementing, and "
         "evaluating public health practice (Klaucke et al., 1988; German et al., 2001). Effective "
         "surveillance systems enable health authorities to detect outbreaks early, locate where "
         "transmission is concentrated, guide targeted interventions, and allocate limited resources "
         "such as medicines, personnel, and supplies to the areas that need them most. Surveillance "
         "is therefore not a record-keeping exercise but the information backbone of outbreak "
         "management: an outbreak that is not detected in time cannot be contained in time, and a "
         "hotspot that is not located cannot be prioritized for response. A study of 41 public "
         "health events in five countries found that only 27 percent met the 7-1-7 target for "
         "timely detection, notification, and response, with most delays occurring at the "
         "municipal and district level (Bochner et al., 2023).")

add_para(doc, "In the Philippines, the Department of Health (DOH) implements the Philippine "
         "Integrated Disease Surveillance and Response (PIDSR) system as the national framework "
         "for monitoring notifiable diseases (DOH, 2014). Although PIDSR provides a standardized "
         "reporting structure and prescribes threshold monitoring and mapping as tasks of local "
         "surveillance units (DOH, 2014, pp. 57, 72), its implementation at "
         "the city epidemiology level remains largely spreadsheet-based and limited in spatial "
         "analysis, automated outbreak detection, and timely notification of responsible "
         "personnel. Surveillance evaluation guidelines emphasize that the usefulness of a "
         "surveillance system depends on its timeliness, data quality, and ability to trigger "
         "public health action (German et al., 2001), highlighting the operational gap that "
         "persists in many local government health offices.")

add_para(doc, "This study develops a Web-Based Disease Outbreak Management System for the City "
         "Epidemiology and Surveillance Unit of Parañaque City. The system is implemented as a "
         "PHP-based web application using the Laravel 8 framework, a MySQL database, Leaflet.js "
         "interactive maps, and Chart.js data visualizations, supported by an internal Python "
         "analytics service that applies established, existing methods for epidemic threshold "
         "detection, spatio-temporal hotspot detection, and trend forecasting. The system is "
         "deployed within the existing DICT-provisioned government server infrastructure of "
         "Parañaque City. The study is aligned with the policies of the Commission on Higher "
         "Education (CHED), which define the professional master's track as culminating in a "
         "capstone project (CHED, 2019) and describe the Master's Capstone Project in Information "
         "Technology as a culminating activity that generates an output useful in the "
         "development of IT solutions, such as application development (CHED, 2010). "
         "Accordingly, the study centers on the design, development, testing, and evaluation of "
         "an operational system rather than on the development of new statistical or machine "
         "learning models.")

add_section(doc, "", "Background of the Study")

add_para(doc, "Parañaque City, as one of the highly urbanized cities in Metro Manila, Philippines, "
         "generates substantial weekly disease data through its network of health centers, "
         "hospitals, and sentinel sites. The City Epidemiology and Surveillance Unit (CESU) is "
         "responsible for monitoring disease trends, investigating unusual increases in cases, and "
         "recommending public health responses to the City Health Officer. The CESU currently "
         "maintains historical PIDSR records spanning 2010 to 2026, comprising approximately "
         "35,000 patient-level cases across the city's 16 barangays and 29 notifiable disease "
         "categories. The CESU processes these surveillance data using manual spreadsheet tools that "
         "offer no geospatial visualization, no automated threshold alerting, no detection of "
         "case clusters, and no mechanism for notifying responsible personnel when an alert "
         "condition arises. Weekly reports, epidemic threshold comparisons, and outbreak memoranda "
         "are compiled by hand, which consumes staff time that could otherwise be spent on case "
         "investigation and response.")

add_para(doc, "The urgency of this gap is compounded by the resource constraints under which local "
         "health units operate. The CESU of Parañaque City has eight personnel: six nurses, one "
         "administrative staff member, and one watchman, so that surveillance work rests on "
         "seven staff members. They serve a population of 723,860 residents and monitor 232 "
         "disease reporting units that submitted PIDSR case reports from 2010 to 2026. Within "
         "the city, these are 16 barangay health centers, 11 hospitals, and the CESU itself, "
         "all of which serve as CESU sentinel sites; outside the city, there are 204 "
         "hospitals, diagnostic laboratories, and other health facilities that diagnosed and "
         "reported cases among Parañaque residents. In 2024 to 2026 alone, 135 of these "
         "units reported at least one case. The "
         "unit operates under an annual budget of _____________ (they are still finalizing), "
         "which must cover case investigation, vector control coordination, "
         "and outbreak response supplies. Under these constraints, every hour spent compiling "
         "spreadsheets and every day of delay in recognizing a hotspot translates into later "
         "response, wider transmission, and a less efficient use of limited medicines, personnel, "
         "and supplies. These local constraints mirror national findings: Philippine local health "
         "units face restrictive hiring policies, budget caps on personnel services, and "
         "workforce migration (Pepito et al., 2025); devolution delays information sharing and "
         "resource allocation (de Claro et al., 2024); and subnational health budgets depend on "
         "central transfers that are often delayed (Ravishankar et al., 2024).")

add_para(doc, "Dengue illustrates the cost of this delay most clearly. Dengue transmission is "
         "spatially concentrated: the Aedes mosquito vector has a limited flight range, so cases "
         "that occur close together in space and time often share a common source of "
         "transmission. For this reason, the CESU applies an operational directive that treats "
         "three or more dengue cases occurring within 200 meters of each other within a four-week "
         "period as a cluster requiring investigation. Applying this rule manually across "
         "thousands of case addresses is impractical, and clusters that straddle barangay "
         "boundaries are invisible in reports that aggregate cases by barangay. Spatio-temporal "
         "analysis that applies this rule automatically, using established density-based "
         "clustering methods (Ester et al., 1996), would allow the CESU to locate hotspots as "
         "soon as cases are encoded. A comparative evaluation of dengue cluster detection methods "
         "in Thailand showed that the choice of method strongly affects which clusters are found "
         "and that polygon-based statistics perform poorly (Rotejanaprasert et al., 2024).")

add_para(doc, "Existing studies on dengue and infectious disease surveillance in the Philippine "
         "context have demonstrated the value of spatial analysis and forecasting. Barangay-level "
         "dengue hotspots in Quezon City were found to be unstable from year to year (Medina et "
         "al., 2023), a national space-time analysis recommended drilling down to the municipal "
         "or barangay level (Olana et al., 2026), and machine learning models have been compared "
         "for dengue forecasting in Metropolitan Manila (Carvajal et al., 2018) and nationwide "
         "(Olana, Poprom, et al., 2025). However, these studies produced "
         "analyses or standalone models without embedding their outputs into an operational, "
         "web-based system that city-level health personnel can use as part of their weekly "
         "workflow, that connects the detection of a hotspot to a recommended response, and that "
         "notifies responsible personnel when action is needed. This gap between demonstrated "
         "analytical capability and operational outbreak management at the local health unit "
         "level provides the direct motivation for this study.")

add_para(doc, "The City Government of Parañaque maintains an Employee Portal at "
         "hrmo.paranaque.gov.ph, provisioned by the Department of Information and Communications "
         "Technology (DICT) and managed by the Human Resource Management Office (HRMO). This "
         "existing infrastructure provides a cost-effective foundation for deploying the system "
         "as a path-based web application under the portal's domain. The system uses the HRMO "
         "portal's existing authentication to confirm that a user is an active city government "
         "employee, but an active HRMO account alone does not grant access: only personnel of "
         "the CESU, a unit of the City Health Office, who have been assigned a role by the "
         "system Administrator can log in, and all other city employees are denied. Because "
         "employment status is maintained by the Human Resource Management Office, access is "
         "revoked automatically when a staff member separates from service. Role-based access control, "
         "audit logging, encryption of data in transit and of backup files, and secure backup "
         "procedures protect the personal and sensitive personal information contained in PIDSR "
         "records, consistent with Republic Act No. 10173, the Data Privacy Act of 2012 "
         "(Republic Act No. 10173, 2012).")

add_para(doc, "The main problem identified in this study is the absence of a web-based disease "
         "outbreak management system for the City Epidemiology and Surveillance Unit of "
         "Parañaque City. Without such a system, health officials face constraints in detecting "
         "anomalous weekly case counts against historical baselines as new case data are encoded, "
         "locating outbreak hotspots at a finer resolution than the barangay, prioritizing "
         "barangays for response, deciding where medicines, personnel, and supplies should be "
         "deployed, and notifying responsible personnel promptly when an alert condition arises. "
         "These limitations reduce the timeliness and spatial precision of public health "
         "interventions at the level where delays in notification and response are most common "
         "(Bochner et al., 2023), in a surveillance system for dengue that remains passive "
         "(Herbuela et al., 2021). The causes of this gap are "
         "multi-layered. Proprietary Geographic Information Systems (GIS) platforms carry "
         "licensing costs for city-level local government unit health offices operating under "
         "fixed annual budgets. The PIDSR Manual of Procedures directs local surveillance units "
         "to compare current case counts against alert and epidemic thresholds and to present "
         "the spatial distribution of cases on maps, preferably through a GIS-enabled system "
         "(DOH, 2014, pp. 57, 72), but it leaves the tools for doing so "
         "to each local unit, and at the city level these tasks remain dependent on spreadsheets. "
         "Finally, local analytical studies have not been translated into operational platforms "
         "accessible to non-technical health personnel at the city level.")

add_para(doc, "In response to the identified problem, this study develops a web-based disease "
         "outbreak management system built entirely on open-source and government-owned "
         "infrastructure. The system follows a single operational chain that mirrors how the "
         "CESU manages an outbreak: it detects unusual increases in cases against epidemic "
         "thresholds, locates spatio-temporal hotspots, prioritizes barangays through a "
         "transparent rule-based risk tier, recommends the deployment of medicines, personnel, "
         "and supplies to Moderate and High risk barangays, and notifies responsible personnel through SMS and "
         "email. The system is developed using PHP 7.4 with the Laravel 8 framework, consistent "
         "with the PHP runtime of the existing HRMO portal, and integrates a Python 3.8 "
         "analytics service developed in FastAPI that applies existing methods, namely the "
         "PIDSR alert and epidemic threshold method (DOH, 2014), the density-based DBSCAN "
         "clustering algorithm, and the open-source Prophet forecasting model (Taylor & Letham, "
         "2018), without developing new models. By deploying the system on the existing "
         "government server, the study avoids additional server procurement, domain "
         "registration, and SSL certificate costs.")

add_section(doc, "", "Objectives of the Study")

add_heading(doc, "General Objective:", level=3, align=WD_ALIGN_PARAGRAPH.LEFT)

add_para(doc, "The general objective of this study is to develop a Web-Based Disease Outbreak "
         "Management System for the City Epidemiology and Surveillance Unit of Parañaque City "
         "that supports the detection, location, prioritization, response recommendation, and "
         "notification of disease outbreaks, deployed within the existing DICT-provisioned "
         "government server infrastructure of Parañaque City.")

add_heading(doc, "Specific Objectives:", level=3, align=WD_ALIGN_PARAGRAPH.LEFT)

add_numbered(doc, 1, "Design the system with the following modules:")
add_sublettered(doc, "a", "Case Data Management for encoding, importing, and validating disease "
             "case records consistent with PIDSR reporting standards.")
add_sublettered(doc, "b", "Disease Mapping using Leaflet.js and OpenStreetMap to display disease "
             "case distribution and incidence across Parañaque City's 16 barangays.")
add_sublettered(doc, "c", "Epidemic Threshold Monitoring that compares weekly case counts against "
             "the PIDSR alert and epidemic thresholds, the disease-specific case triggers of the "
             "PIDSR Manual of Procedures, and the CESU five-year average, and flags alert "
             "conditions automatically.")
add_sublettered(doc, "d", "Spatio-Temporal Hotspot Detection that applies the CESU cluster rule "
             "of three or more cases within 200 meters and four weeks using the DBSCAN "
             "algorithm.")
add_sublettered(doc, "e", "Disease Trend Forecasting that presents near-term probable case trends "
             "using the existing Prophet forecasting model.")
add_sublettered(doc, "f", "Risk Prioritization and Resource Allocation Recommendation that "
             "classifies barangays into High, Moderate, and Low risk tiers through transparent "
             "rules and recommends the deployment of medicines, personnel, and supplies to "
             "barangays classified as Moderate or High risk.")
add_sublettered(doc, "g", "Outbreak Alerts and Notifications that inform designated personnel "
             "through SMS and email when an alert condition is detected.")
add_sublettered(doc, "h", "Surveillance Reports and Data Export that generate the weekly PIDSR "
             "surveillance report, outbreak memoranda, and role-tiered data exports.")
add_sublettered(doc, "i", "Security and System Administration that provides role-based access "
             "control, audit logging, encryption of data in transit and of backup files, and "
             "secure backup and restoration procedures.")

add_numbered(doc, 2, "Develop the system using PHP 7.4 as the server-side language with the "
             "Laravel 8 framework; MySQL 8 as the relational database management system; React "
             "for the user interface; Leaflet.js with OpenStreetMap tiles for interactive, "
             "license-free web mapping; "
             "Chart.js for trend visualization; Python 3.8 with FastAPI as an internal analytics "
             "service that applies the existing DBSCAN clustering algorithm and Prophet "
             "forecasting model; an SMS gateway and email service for notifications; and HRMO "
             "portal authentication combined with a CESU staff authorization list that restricts "
             "access to authorized CESU personnel of the City Health Office, all deployed within "
             "the existing DICT-provisioned server infrastructure.")

add_numbered(doc, 3, "Test the developed system using defined test cases with measurable pass "
             "criteria in the following areas:")
add_sublettered(doc, "a", "Case encoding, import, validation, and audit logging.")
add_sublettered(doc, "b", "Barangay-level mapping and aggregation.")
add_sublettered(doc, "c", "Epidemic threshold computation and alert generation.")
add_sublettered(doc, "d", "Spatio-temporal hotspot detection.")
add_sublettered(doc, "e", "Trend forecast retrieval and display.")
add_sublettered(doc, "f", "Risk tier classification and resource allocation recommendation.")
add_sublettered(doc, "g", "SMS and email notification delivery.")
add_sublettered(doc, "h", "Weekly report generation and data export.")
add_sublettered(doc, "i", "Authentication, role-based access control, encryption, and backup "
             "and restoration.")

add_numbered(doc, 4, "Evaluate the level of acceptability of the developed system using an "
             "ISO/IEC 25010:2023-based software evaluation instrument administered to purposively "
             "selected CESU and City Health Office personnel and IT professionals in terms of "
             "functional suitability, performance efficiency, interaction capability, "
             "reliability, security, and maintainability, and validate the system's outputs with "
             "CESU personnel as domain experts.")

add_section(doc, "", "Significance of the Study")

add_para(doc, "The development of the system addresses a concrete and documented operational gap "
         "in the outbreak management capacity of the City Epidemiology and Surveillance Unit of "
         "Parañaque City. By providing an integrated web-based platform that detects, locates, "
         "prioritizes, recommends, and notifies, this study aims to equip health officials with "
         "tools that directly improve the speed, spatial precision, and coordination of outbreak "
         "response. Its significance is particularly pronounced because it is designed for "
         "deployment on existing government infrastructure without additional licensing costs, "
         "making it a sustainable and replicable model for other city local government units "
         "facing similar surveillance limitations.")

add_para(doc, "The City Epidemiology and Surveillance Unit and its health officials are the primary "
         "direct beneficiaries of the system. It streamlines the translation of raw PIDSR case "
         "records into maps, alerts, and reports; reduces the manual workload associated with "
         "weekly data compilation and report preparation; and brings potential outbreaks to the "
         "attention of responsible personnel through automated notifications rather than through "
         "manual review. Health officers and city health decision-makers who currently rely on "
         "spreadsheet summaries benefit from a consolidated dashboard that presents disease "
         "distribution, threshold status, hotspots, risk tiers, and recommended responses in a "
         "single interface accessible through any web browser.")

add_para(doc, "The City Health Office benefits from more efficient allocation of limited "
         "resources. Because the system recommends where medicines, personnel, and supplies "
         "should be deployed on the basis of detected hotspots and risk tiers, decisions on "
         "resource deployment can be grounded in current surveillance evidence and documented "
         "for accountability.")

add_para(doc, "The residents of Parañaque City are the ultimate beneficiaries of improved "
         "outbreak management. Earlier detection of unusual increases in cases, faster location "
         "of hotspots, and prompt notification of responsible personnel translate into faster "
         "public health response, more targeted intervention in high-risk barangays, and more "
         "efficient use of limited public health resources. In a densely populated urban setting "
         "such as Parañaque City, where diseases such as dengue, measles, and leptospirosis "
         "present recurring seasonal threats, the ability to respond to outbreaks proactively "
         "rather than reactively has direct implications for reducing morbidity and mortality.")

add_para(doc, "Beyond its immediate operational impact, this study contributes to the applied "
         "information technology literature in Philippine public health. By demonstrating that an "
         "open-source, PHP- and Python-based architecture can deliver spatial analysis, automated "
         "alerting, hotspot detection, response recommendation, and notification on a "
         "government-owned server without proprietary GIS licensing, the study provides a "
         "technically documented and evaluated precedent for cost-effective digital outbreak "
         "management at the city level in the Philippines. Future researchers may use the system "
         "and its documentation as a basis for extending outbreak management tools to other "
         "local government units and diseases.")

add_section(doc, "", "Scope and Limitations of the Study")

add_para(doc, "This study covers the design, development, testing, and evaluation of a Web-Based "
         "Disease Outbreak Management System for the City Epidemiology and Surveillance Unit of "
         "Parañaque City. The system is deployed as a path-based web application under the "
         "domain of the existing DICT-provisioned server used by the Parañaque City HRMO portal. "
         "The study makes use of historical PIDSR disease case data provided by the City "
         "Epidemiology and Surveillance Unit, covering the years 2010 to 2026 and comprising "
         "approximately 35,000 patient-level records across the city's 16 barangays and 29 "
         "notifiable disease categories.")

add_para(doc, "The scope of the system includes nine modules: case data management; disease "
         "mapping; epidemic threshold monitoring; spatio-temporal hotspot detection; disease "
         "trend forecasting; risk prioritization and resource allocation recommendation; outbreak "
         "alerts and notifications through SMS and email; surveillance reports and data export; "
         "and security and system administration. The analytical functions of the system apply "
         "existing and established methods. The study does not develop, train, tune, or "
         "benchmark new statistical or machine learning models.")

add_para(doc, "The study is subject to the following limitations:")
add_lettered(doc, "a", "The trend forecasts of the system indicate probable trends in case counts "
             "and do not predict the exact occurrence, timing, or magnitude of an outbreak.")
add_lettered(doc, "b", "The outputs of the system depend on the completeness and timeliness of "
             "the PIDSR records encoded by reporting facilities; missing, delayed, or inconsistent "
             "reports reduce the accuracy of thresholds, hotspots, and forecasts.")
add_lettered(doc, "c", "Hotspot detection depends on the accuracy of case addresses. Cases whose "
             "addresses cannot be located with sufficient precision are excluded from spatial "
             "clustering but remain in barangay-level counts.")
add_lettered(doc, "d", "Forecasting and hotspot detection are limited to the diseases included in "
             "the dataset, and forecasts are displayed only for diseases for which the "
             "forecasting model outperforms a simple same-week-last-year comparison on "
             "historical data.")
add_lettered(doc, "e", "The resource allocation recommendations are rule-based guidance derived "
             "from detected hotspots and risk tiers. They do not replace the decisions of the "
             "City Health Officer and do not track the actual inventory of medicines and "
             "supplies.")
add_lettered(doc, "f", "The system is a decision-support tool. It is not intended to replace "
             "physician diagnosis or the professional judgment of trained epidemiologists, and it "
             "does not override the outbreak declaration authority of the City Health Officer in "
             "coordination with the DOH Regional Epidemiology and Surveillance Unit.")
add_lettered(doc, "g", "SMS notification depends on the availability of an SMS gateway and its "
             "associated cost; email notification depends on the availability of the email "
             "service of the City Government.")
add_lettered(doc, "h", "The system is limited to the 16 barangays of Parañaque City and does not "
             "include cases from adjacent cities recorded in the dataset. It does not integrate "
             "in real time with the national DOH PIDSR electronic reporting portal and does not "
             "include clinical patient management or biometric data processing.")
add_lettered(doc, "i", "Evaluation is conducted using an ISO/IEC 25010:2023-based instrument "
             "administered to purposively selected CESU and City Health Office personnel and IT "
             "professionals within a defined evaluation period. The study does not include "
             "long-term deployment monitoring or high-concurrency stress testing.")

# =================================================================
#                     CHAPTER 2
# =================================================================
add_chapter_break(doc, "Chapter 2", "CONCEPTUAL FRAMEWORK")

add_section(doc, "", "Review of Related Studies and Literature")

add_para(doc, "This chapter presents the literature and studies that provide the conceptual and "
         "empirical foundations of the system. The conceptual literature is organized around the "
         "public health and technical domains the system addresses: disease surveillance, digital "
         "surveillance at the local level, geographic information systems, epidemic thresholds, "
         "spatio-temporal hotspot detection, forecasting with existing models, decision support for "
         "resource allocation, outbreak notification, data security and privacy, the resource "
         "constraints of local health units, and software quality evaluation. Related foreign and "
         "local studies and systems are then reviewed, and a thematic gap analysis identifies the "
         "gap that the study addresses. The chapter concludes with the conceptual framework and the "
         "operational definition of terms.")

add_section(doc, "2.1.1", "Disease Surveillance and the PIDSR Framework")
add_para(doc, "Public health surveillance is defined as the ongoing, systematic collection, "
         "analysis, interpretation, and dissemination of health data essential for planning, "
         "implementing, and evaluating public health practice (Klaucke et al., 1988; German et al., "
         "2001). Surveillance systems are commonly described as passive, when health facilities "
         "report cases on their own initiative, or active, when the health agency seeks out cases "
         "(Klaucke et al., 1988). Guidelines for evaluating surveillance systems identify "
         "timeliness, data quality, and usefulness for public health action among the attributes "
         "that determine the value of a surveillance system, and note that the increasing use of "
         "electronic data collection might promote timeliness (German et al., 2001). The World "
         "Health Organization likewise frames early warning and response as the rapid detection, "
         "assessment, and response to acute public health events (WHO, 2014).")
add_para(doc, "In the Philippines, the Department of Health implements the Philippine Integrated "
         "Disease Surveillance and Response (PIDSR) system as the national disease notification "
         "framework. Under PIDSR, disease reporting units report cases of notifiable diseases using "
         "standardized case investigation forms that capture disease, classification, outcome, "
         "patient characteristics, reporting facility, and address (DOH, 2014). The PIDSR Manual of "
         "Procedures assigns analysis to the local epidemiology and surveillance unit: it directs "
         "the unit to compare current counts against an alert threshold and an epidemic threshold "
         "(DOH, 2014, p. 57) and recommends that the spatial distribution of cases be presented on "
         "maps, preferably through a GIS-enabled system (DOH, 2014, p. 72). Philippine dengue "
         "surveillance in particular remains passive, relying on notifications that flow from "
         "barangays and hospitals to city offices (Herbuela et al., 2021). The system developed in "
         "this study is designed as an analytical and response layer on top of PIDSR data, "
         "performing the analysis the manual assigns to the CESU without replacing or duplicating "
         "the national reporting workflow.")

add_section(doc, "2.1.2", "Digital and Web-Based Surveillance at the Local Level")
add_para(doc, "Electronic surveillance platforms consistently improve the completeness of "
         "reporting and, to a lesser degree, its timeliness. In mainland Tanzania, weekly "
         "completeness of the electronic Integrated Disease Surveillance and Response system rose "
         "above 90 percent, and the authors concluded that it could support early outbreak "
         "detection (Joseph et al., 2022). In ten local government areas of northeast Nigeria, an "
         "electronic reporting platform more than doubled the number of reporting facilities and "
         "raised reporting timeliness from 43 to 73 percent (Ibrahim et al., 2021). The national "
         "roll-out of DHIS2 in Guinea achieved high completeness of aggregate reporting, although "
         "case-based reporting and workforce capacity remained limiting (Reynolds et al., 2022).")
add_para(doc, "Implementation studies show, however, that these gains depend on infrastructure, "
         "funding, and local software capacity rather than on algorithms. In Ghana, the "
         "implementation of a digital outbreak response system was hampered by unstable "
         "interoperability, reliance on a private company for hosting, unreliable internet and "
         "power, and dependence on external funding (Kaburi et al., 2023). In the Philippines, "
         "timely submission of routine health reports in Palawan improved only after deadlines were "
         "extended, and the authors recommend interventions that extend existing routines rather "
         "than replace them (Murai et al., 2022). Primary care facilities in Manila scored low on "
         "health information system governance and cited inadequate training and resources as "
         "barriers (Sucaldito et al., 2025). The most advanced local government platform "
         "documented in the country, an open-source health information exchange piloted in three "
         "local government units, demonstrated that locally hosted platforms are feasible, but it "
         "addresses data exchange rather than outbreak analytics (Zuniga et al., 2026). These "
         "findings support the design of the system as a locally hosted platform built on the "
         "existing PIDSR workflow and maintainable with the City Government's own resources.")

add_section(doc, "2.1.3", "Geographic Information Systems and Disease Mapping")
add_para(doc, "Geographic Information Systems are computer-based platforms for capturing, "
         "storing, analyzing, and displaying geographically referenced data. A review of GIS "
         "applications in health promotion and public health documented their use for mapping "
         "disease distribution, assessing access to services, and supporting the planning of "
         "interventions (Nykiforuk & Flaman, 2011). In spatial epidemiology, disease mapping "
         "methods are used to estimate the geographic variation of risk and to detect clustering "
         "of cases (Lawson, 2018). A scoping review of GIS for dengue surveillance found that risk "
         "mapping and hotspot detection were the most common applications, followed by vector "
         "control, and that GIS has evolved from a mapping tool into a decision-support system "
         "with real-time monitoring and early warning as emerging trends (Prakash Nayak et al., "
         "2025).")
add_para(doc, "Free and open-source GIS tools have lowered the barrier to adoption for "
         "resource-constrained health agencies. Fisher and Myers (2011) showed that free GIS tools "
         "allowed district and clinic health staff in a low-resource setting to map health "
         "indicators and use the results for planning, concluding that GIS can be an inexpensive "
         "tool for decentralizing health data analysis. Leaflet.js, the open-source JavaScript "
         "library used in this study, extends this approach to the web browser without requiring "
         "client-side software installation, and OpenStreetMap provides base map data without "
         "licensing costs. The system renders disease distribution as a barangay-level choropleth "
         "because public health response in Parañaque City is organized by barangay and because "
         "barangay rates can be compared against population denominators; finer spatial structure "
         "is captured separately by the spatio-temporal hotspot detection described below.")

add_section(doc, "2.1.4", "Epidemic Thresholds and Automated Outbreak Detection")
add_para(doc, "Outbreak detection in routine surveillance commonly relies on aberration detection "
         "methods that compare current case counts with historical baselines. The historical "
         "limits method compares the current count with the mean and standard deviation of "
         "comparable periods in previous years (Stroup et al., 1989). The PIDSR Manual of "
         "Procedures prescribes this approach for local units: the alert threshold is the weekly "
         "or monthly average of the past three to five years plus one standard deviation, and the "
         "epidemic threshold is the same average plus two standard deviations (DOH, 2014, p. 57). "
         "For certain diseases, such as measles and acute flaccid paralysis, the manual instead "
         "treats a single case as an alert (DOH, 2014, p. 58). The epidemic threshold is "
         "expressed as follows:")
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
set_double_spacing(p)
r = p.add_run("Epidemic if: Current Cases > Baseline Mean + 2 × Standard Deviation")
r.italic = True
r.font.name = "Times New Roman"
r.font.size = Pt(12)
add_para(doc, "The Early Aberration Reporting System of the United States Centers for Disease "
         "Control and Prevention applies the same family of baseline-plus-standard-deviation "
         "methods with short moving baselines (Hutwagner et al., 2003), and its algorithms have "
         "been used in Brazil to anticipate dengue outbreaks in municipalities up to four weeks "
         "before case notification (Santos-Silva et al., 2025). Threshold-based alerting must "
         "balance sensitivity against false alarms. In Puerto Rico, a historical-baseline dengue "
         "threshold was chosen for the best balance between false alarms and missed detections "
         "and was used prospectively to support a public health emergency declaration (Thayer et "
         "al., 2025). A systematic review of dengue early warning systems reported sensitivity "
         "from 50 to 100 percent and positive predictive values from 43 to 86 percent, and noted "
         "that their usefulness depends heavily on timely, high-quality surveillance data "
         "(Baharom et al., 2022). The system automates the PIDSR thresholds for all monitored "
         "diseases and displays them alongside the CESU five-year average, keeping the alert "
         "logic transparent to CESU personnel.")

add_section(doc, "2.1.5", "Spatio-Temporal Hotspot Detection")
add_para(doc, "Dengue transmission is spatially and temporally concentrated, and identifying "
         "where cases cluster allows vector control and case investigation to be targeted. "
         "Comparative evaluations of cluster detection methods on national dengue data in "
         "Thailand found that polygon-based statistics such as Getis-Ord and Moran's I performed "
         "poorly, that scan statistics with rigid windows tended to flag oversized clusters, and "
         "that space-time interaction matters for detection (Rotejanaprasert et al., 2024). In "
         "Peninsular Malaysia, space-time scan statistics identified dengue clusters that "
         "extended from dense districts into their neighbors, making vector-control decisions "
         "more objective (Abd Naeeim & Abdul Rahman, 2022), and subdistrict analysis in Thailand "
         "showed that district-level programs mask high-risk subdistricts (Rattananen et al., "
         "2025).")
add_para(doc, "Density-Based Spatial Clustering of Applications with Noise (DBSCAN) groups points "
         "that lie within a specified distance of each other when a minimum number of points is "
         "reached, and treats isolated points as noise (Ester et al., 1996). Because its two "
         "parameters correspond directly to a distance and a case count, DBSCAN can express an "
         "operational cluster rule such as the CESU rule of three or more cases within 200 meters. "
         "A recent application of DBSCAN to dengue across Brazilian municipalities found it "
         "reproducible and operationally relevant for guiding vector control, with parameters "
         "chosen through sensitivity analysis (Sena et al., 2025). The system applies DBSCAN to "
         "geocoded case addresses within rolling four-week windows, so that clusters are defined "
         "by the distance between cases rather than by administrative boundaries.")

add_section(doc, "2.1.6", "Disease Trend Forecasting with Existing Models")
add_para(doc, "Prophet is an open-source forecasting model developed by Meta that decomposes a "
         "time series into trend, seasonal, and holiday components fitted through an additive "
         "regression model, and is designed to be robust to missing data and to be used by "
         "analysts without specialized time-series expertise (Taylor & Letham, 2018). Recent "
         "comparative studies show that Prophet is a practical but not universally superior "
         "option. For national dengue forecasting in the Philippines, Prophet performed worse "
         "than a seasonal-naive benchmark, while neural network autoregression and Random Forest "
         "performed best (Olana, Poprom, et al., 2025). In Uganda, ARIMA outperformed Prophet for "
         "malaria incidence nationally and in most regions, although both were judged usable for "
         "guiding resource allocation (Fuller et al., 2025). In Bangladesh, no single model was "
         "best at every horizon: SARIMAX was best for one-step outbreak alerting, while Prophet "
         "was best for pooled forecasts two to six steps ahead (Fuad et al., 2026). In Rio de "
         "Janeiro, Prophet performed best at the 12-week horizon among several statistical and "
         "machine learning models (Chen & Moraga, 2025).")
add_para(doc, "In the Philippine context, Carvajal et al. (2018) compared several statistical and "
         "machine learning methods for dengue in Metropolitan Manila and found Random Forest to "
         "perform best, but, like the national study of Olana, Poprom, et al. (2025), produced "
         "standalone models rather than tools used in routine surveillance. These findings shape "
         "two design decisions of the system. First, forecasting is presented as a probable trend "
         "and kept separate from alerting, which relies on the transparent PIDSR thresholds. "
         "Second, because Prophet does not perform well on every disease, the forecast is displayed "
         "only for diseases for which it outperforms a simple same-week-last-year comparison on "
         "historical data, an operational safeguard rather than a model development activity.")

add_section(doc, "2.1.7", "Decision Support for Outbreak Response and Resource Allocation")
add_para(doc, "Hotspot detection is repeatedly justified as an input to resource allocation. "
         "Spatio-temporal analysis of dengue in Vietnam was presented as a basis for optimizing "
         "resource allocation in resource-constrained settings (Osako et al., 2026). On Bioko "
         "Island, a spatial decision support system that guided indoor residual spraying at fine "
         "spatial granularity and tracked field teams in real time raised operational efficiency "
         "and reduced overspraying (García et al., 2022). In India, a single mobile and web tool "
         "combined disease surveillance with workforce and supply chain management and improved "
         "the accountability of stocks (Rajvanshi et al., 2021). In Brazil, historical thresholds "
         "combined with climate data were used to sequence vector-control measures region by "
         "region (Gouveia et al., 2025). A multi-model study for county-level outbreak decisions "
         "found that models differing in magnitude still agreed on the ranking of interventions, "
         "supporting the presentation of ranked recommendations rather than precise quantities "
         "(Shea et al., 2023).")
add_para(doc, "The evidence on which response works best remains uncertain. A meta-review found "
         "insufficient evidence to recommend a single dengue vector-control method and stressed "
         "the importance of vector-control management by local governments (Low et al., 2025), and "
         "a cluster-randomized trial of targeted integrated vector management in urban Malaysia "
         "found no significant reduction in overall incidence (Saadatian-Elahi et al., 2025). For "
         "this reason, the resource allocation function of the system is designed as a "
         "transparent, knowledge-based recommender whose rules are encoded from DOH and WHO "
         "response guidance, validated with CESU personnel, and maintained by the Administrator, "
         "supporting rather than replacing the judgment of CESU personnel.")

add_section(doc, "2.1.8", "Outbreak Alerts and Notification")
add_para(doc, "Detection is useful only when it reaches the people who must respond. Across 41 "
         "public health events in five countries, only 27 percent met the 7-1-7 target for "
         "detection, notification, and response, and delays in notification and response were "
         "most often found at the intermediate level, that is, at the municipal, district, or "
         "provincial tier (Bochner et al., 2023). In Uganda, weekly reporting through an SMS-based "
         "system did not by itself achieve timely reporting, and the urban capital had the lowest "
         "timeliness of all districts (Nansikombi et al., 2023).")
add_para(doc, "Low-cost notification channels can narrow this gap. In New South Wales, "
         "personalized two-way SMS achieved the highest response rate among the contact methods "
         "used in salmonellosis surveillance and supported the detection of ten outbreaks under "
         "resource constraints (Franklin et al., 2025). In Houston, a city health department "
         "built a text- and email-based alert system from existing city resources and sent more "
         "than five thousand alerts within six months (Schneider et al., 2025). In the "
         "Philippines, an early warning surveillance system piloted in jails in Calabarzon "
         "reported most events within 24 hours and prompted local health units to respond with "
         "medicines and infection control, while documenting insufficient workforce and slow "
         "internet as challenges (Manahan et al., 2024). Because frequent or duplicate alerts can "
         "erode attention, the system limits notifications to one per disease, barangay, alert "
         "type, and week, a design safeguard informed by the attention to false alarms in the "
         "threshold literature (Thayer et al., 2025).")

add_section(doc, "2.1.9", "Data Security and Privacy in Health Information Systems")
add_para(doc, "Republic Act No. 10173, the Data Privacy Act of 2012, classifies health "
         "information as sensitive personal information and requires personal information "
         "controllers to implement reasonable and appropriate organizational, physical, and "
         "technical measures to protect personal information against unauthorized access, "
         "disclosure, and alteration (Republic Act No. 10173, 2012, Secs. 3, 20). The National "
         "Privacy Commission specifies these measures for government and private entities in NPC "
         "Circular No. 2023-06, which superseded NPC Circular No. 16-01 (NPC, 2023), and requires "
         "that personal data breaches be reported to the Commission and to affected data subjects "
         "within 72 hours of knowledge of the breach (NPC, 2016).")
add_para(doc, "The threat environment makes these controls necessary rather than optional. "
         "Ransomware attacks on health care delivery organizations in the United States doubled "
         "between 2016 and 2021, exposed the health information of nearly 42 million patients, and "
         "most often disrupted care through electronic system downtime (Neprash et al., 2022). "
         "Reviews of health care cybersecurity identify phishing, ransomware, and malware as "
         "dominant threats and call for layered technical protections and staff training (He et "
         "al., 2021). Audit logs, as time-sequenced records of user activity, support both "
         "accountability and the evaluation of system use (Kannampallil & Adler-Milstein, 2022). "
         "Public health agencies have reduced re-identification risk by suppressing fields and "
         "maintaining tiered access to case data (Lee et al., 2021), and the use of case-location "
         "maps during the COVID-19 response in Asia showed that spatial surveillance creates "
         "privacy obligations that must be balanced against public health benefit (Nageshwaran et "
         "al., 2021). These findings inform the role-based access control, audit logging, "
         "encryption, secure backup, and data minimization measures of the system.")

add_section(doc, "2.1.10", "Resource Constraints of Local Health Units")
add_para(doc, "Philippine local health units operate under constraints that make the automation "
         "of routine analysis urgent. Restrictive government hiring policies, budget caps on "
         "personnel services, uncompetitive salaries, a lack of trained personnel, and overseas "
         "migration constrain the health workforce at the local level (Pepito et al., 2025). "
         "Devolution has fragmented coordination and delayed information sharing and resource "
         "allocation between levels of government (de Claro et al., 2024), and subnational health "
         "budgets depend on central transfers that are often delayed (Ravishankar et al., 2024). "
         "Public health workers reported work overload, stress, and pressure to learn new "
         "technologies during the COVID-19 response (Maravilla et al., 2023), and when the staff "
         "of the national antimicrobial resistance surveillance program were diverted to the "
         "pandemic, automated data submission was identified as key to sustaining surveillance "
         "(Boehme et al., 2022). In Metro Manila, a regional surveillance unit cut report "
         "turnaround from 31 to 8 minutes through low-cost dashboards while working under staffing "
         "and budget limits (Ong, 2026). These conditions mean that the CESU cannot simply add "
         "personnel to keep pace with surveillance workload; tools that automate routine analysis "
         "and notification are a practical response.")

add_section(doc, "2.1.11", "Software Quality Evaluation")
add_para(doc, "ISO/IEC 25010:2023 defines an international product quality model consisting of "
         "nine characteristics: functional suitability, performance efficiency, compatibility, "
         "interaction capability (formerly usability), reliability, security, maintainability, "
         "flexibility, and safety (International Organization for Standardization & International Electrotechnical Commission [ISO/IEC], 2023). The model has been used to appraise electronic "
         "health record systems, where a systematic review found that usability was the most "
         "frequently assessed characteristic and security the least (Al Ani et al., 2022). In "
         "Peru, a usability instrument based on ISO 25010 was developed and validated with "
         "physicians, nurses, and administrative staff, with emphasis on alignment with national "
         "regulation (Mamani-Pari et al., 2026). In the Philippines, a study of electronic health "
         "record acceptance among health workers found high intention to use and identified "
         "self-efficacy as the significant predictor, underscoring the value of co-production and "
         "training (De Mesa et al., 2024). Following these precedents, the system is evaluated "
         "against six ISO/IEC 25010:2023 characteristics, including security, by its intended "
         "users and by IT professionals.")

add_section(doc, "", "Foreign Studies")
add_para(doc, "Foreign studies demonstrate the separate strengths of each component of the "
         "system. Threshold-based early warning has been validated prospectively: in Puerto Rico, "
         "a dengue alert threshold built from routine surveillance data supported an emergency "
         "declaration (Thayer et al., 2025), and in Mexico and Colombia an early warning and "
         "response system achieved high sensitivity for dengue alarms with several weeks of lead "
         "time, although its validity varied by disease (Cardenas et al., 2022). Spatio-temporal "
         "cluster detection has been compared rigorously on national dengue data, showing that the "
         "choice of method strongly affects which clusters are found (Rotejanaprasert et al., "
         "2024), and density-based clustering has been applied to dengue to guide vector control "
         "(Sena et al., 2025).")
add_para(doc, "Studies of notification and response show that the intermediate level, where "
         "city units such as the CESU sit, is where delays most often occur (Bochner et al., "
         "2023), and that SMS and email channels built from existing resources can deliver alerts "
         "at scale (Franklin et al., 2025; Schneider et al., 2025). Spatial decision support has "
         "improved the deployment of vector-control resources and personnel (García et al., "
         "2022). Reviews of artificial intelligence in early warning conclude that the barriers to "
         "real-world use are now data quality, interpretability, integration into surveillance "
         "systems, and privacy rather than the availability of methods (Villanueva-Miranda et al., "
         "2025), and that temporal forecasting, spatial analysis, and threshold alerting are usually "
         "built as separate models rather than as one operational system (Hu et al., 2025).")

add_section(doc, "", "Local Studies")
add_para(doc, "Philippine studies establish both the need for and the feasibility of city-level "
         "outbreak tools. Nationwide analyses found persistently high dengue case intensity in the "
         "National Capital Region and recommended risk-based, geospatially targeted surveillance "
         "(Olana, Thongprachum, et al., 2025), and a national space-time analysis of 2017 to 2024 "
         "data recommended drilling down to municipal or barangay level for targeting (Olana et "
         "al., 2026). In Quezon City, a neighboring Metro Manila city, eighteen barangays were "
         "identified as dengue hotspots, but hotspot membership was unstable from year to year "
         "(Medina et al., 2023), and hotspots shifted again between the periods before and after "
         "the COVID-19 pandemic (Medina et al., 2025). In South Cotabato, space-time scan "
         "statistics identified significant dengue clusters and the authors recommended targeted "
         "interventions and real-time surveillance (Ygoña et al., 2025). These studies are "
         "retrospective and aggregate cases to barangay or provincial units, so clusters that "
         "cross barangay boundaries cannot be seen, and none delivered a working tool to a local "
         "health unit.")
add_para(doc, "Forecasting studies in the Philippines have likewise produced standalone models. "
         "Carvajal et al. (2018) found Random Forest the best performer for dengue in Metropolitan "
         "Manila, and Olana, Poprom, et al. (2025) benchmarked six models nationally and found "
         "that Prophet did not outperform a seasonal-naive benchmark. Studies of the health system "
         "document the conditions under which any tool must operate: chronically late routine "
         "reporting (Murai et al., 2022), weak local health information system governance "
         "(Sucaldito et al., 2025), workforce restrictions and migration (Pepito et al., 2025), "
         "fragmented coordination under devolution (de Claro et al., 2024), and workforce strain "
         "(Maravilla et al., 2023). Philippine surveillance units have nevertheless improved "
         "timeliness with low-cost digital tools (Ong, 2026; Manahan et al., 2024), showing that "
         "locally built systems are feasible when they fit existing workflows.")

add_section(doc, "", "Foreign Systems")
add_para(doc, "HealthMap processes internet-based reports through automated classification and "
         "displays emerging disease threats on a global map, demonstrating automated detection "
         "as a complement to traditional surveillance at a global scale (Freifeld et al., 2008). "
         "The Early Aberration Reporting System of the Centers for Disease Control and Prevention "
         "provides publicly documented threshold-based aberration detection (Hutwagner et al., "
         "2003). The Early Warning and Response System for dengue in Mexico was integrated in "
         "stages into the national surveillance platform, an integration the authors describe as "
         "rarely achieved (Sanchez Tejeda et al., 2023). The Johns Hopkins University COVID-19 "
         "dashboard aggregated case reports from multiple sources into a public web map, showing "
         "that map-based surveillance dashboards can make data accessible in near real time (Dong "
         "et al., 2020). Each system covers part of the outbreak management cycle, but none "
         "combines case-level hotspot detection, resource recommendation, and notification for a "
         "city health unit.")

add_section(doc, "", "Local Systems")
add_para(doc, "Nationally, PIDSR provides the case notification framework and prescribes "
         "threshold monitoring and mapping as local tasks without providing the local tools to "
         "perform them (DOH, 2014). During the COVID-19 pandemic, the DOH DataCollect Bed Tracker "
         "collected bed, ventilator, human resource, and supplies data from 1,906 facilities "
         "through a web application, showing that web-based surveillance of resources is "
         "achievable with available technology (Cabaro et al., 2023). An open-source, "
         "standards-based local health information exchange was piloted in three local "
         "government units and provided real-time dashboards (Zuniga et al., 2026). The Mozzify "
         "application was developed for the early detection of dengue outbreaks and was rated "
         "highly in a usability study that included health professionals (Herbuela et al., 2021). "
         "Table 1 compares these systems with the system developed in this study on the "
         "capabilities required for city-level outbreak management.")
add_table(doc, 1, "Comparison of Related Systems with the Developed System",
          ["Capability", "EARS", "EWARS (Mexico)", "JHU Dashboard", "PIDSR", "DataCollect",
           "LGU Health Exchange", "This Study"],
          [
              ("Case data management", "–", "–", "Aggregate", "Yes", "Yes", "Yes", "Yes"),
              ("Map display", "–", "–", "Yes", "Manual", "–", "–", "Yes"),
              ("Automated threshold alerts", "Yes", "Yes", "–", "Manual", "–", "–", "Yes"),
              ("Case-level spatio-temporal hotspots", "–", "–", "–", "–", "–", "–", "Yes"),
              ("Trend forecasting", "–", "Yes", "–", "–", "–", "–", "Yes"),
              ("Resource allocation", "–", "–", "–", "–", "Tracking", "–",
               "Recommends"),
              ("SMS and email notification", "–", "–", "–", "–", "–", "–", "Yes"),
              ("Hosted by the local government unit", "–", "–", "–", "–", "–", "Yes", "Yes"),
          ],
          widths=[1.35, 0.62, 0.72, 0.72, 0.62, 0.78, 0.82, 0.82], font_size=8.5)
add_para(doc, "In Table 1, a dash indicates that the capability is not reported in the reviewed "
         "source, and Manual indicates a task the PIDSR Manual of Procedures assigns to local "
         "units without providing a tool (DOH, 2014; Hutwagner et al., 2003; Sanchez Tejeda et "
         "al., 2023; Dong et al., 2020; Cabaro et al., 2023; Zuniga et al., 2026).",
         first_line_indent=0)

add_section(doc, "", "Thematic Gap Analysis")
add_para(doc, "As recommended by the panel, the reviewed literature was synthesized through "
         "thematic analysis, following the phases described by Braun and Clarke (2006): "
         "familiarization with the sources, initial coding of each source's findings and "
         "limitations, grouping of codes into candidate themes, review of the themes against the "
         "coded sources, definition and naming of the themes, and reporting. Five themes emerged. "
         "Table 2 summarizes what the literature establishes under each theme and the gap that "
         "remains for a city epidemiology and surveillance unit.")
add_table(doc, 2, "Themes Identified in the Reviewed Literature and Remaining Gaps",
          ["Theme", "What the Literature Establishes", "Remaining Gap"],
          [
              ("Digitization without analysis",
               "Electronic reporting improves completeness and timeliness (Joseph et al., 2022; "
               "Ibrahim et al., 2021); adoption depends on infrastructure and local capacity "
               "(Kaburi et al., 2023; Zuniga et al., 2026).",
               "Digitized PIDSR data are still analyzed by hand at the city level."),
              ("Spatial analysis that stops at description",
               "Cluster methods for dengue are mature (Rotejanaprasert et al., 2024; Sena et al., "
               "2025); Philippine hotspots are persistent yet unstable (Medina et al., 2023; "
               "Olana et al., 2026).",
               "No tool applies the case-address 200-meter, four-week rule; cross-barangay "
               "clusters stay invisible."),
              ("Alerts that do not reach responders",
               "Threshold alerting is validated (Thayer et al., 2025; Cardenas et al., 2022); "
               "delays concentrate at the municipal level (Bochner et al., 2023); SMS and email "
               "work (Franklin et al., 2025; Schneider et al., 2025).",
               "Thresholds, hotspots, and notification are not connected in one city workflow."),
              ("Decision support without a resource recommender",
               "Spatial decision support improves deployment (García et al., 2022); evidence for "
               "any single control method is limited (Low et al., 2025).",
               "No study maps detected hotspots to recommended medicines, personnel, and supplies "
               "for a city unit."),
              ("Constraints that make integration urgent",
               "Workforce, budget, and coordination limits (Pepito et al., 2025; de Claro et al., "
               "2024; Ravishankar et al., 2024); rising security threats (Neprash et al., 2022).",
               "City units need automation that is locally hosted, secure, and compliant with the "
               "Data Privacy Act."),
          ],
          widths=[1.45, 3.05, 2.0], font_size=9)
add_para(doc, "The first theme, digitization without analysis, shows that electronic reporting "
         "platforms improve completeness and timeliness (Joseph et al., 2022; Ibrahim et al., "
         "2021) but that their benefits depend on infrastructure, funding, and in-country "
         "software capacity (Kaburi et al., 2023). In the Philippines, routine reporting has been "
         "chronically late (Murai et al., 2022), local health information systems remain "
         "fragmented and weakly governed (Sucaldito et al., 2025), and the most advanced "
         "documented local platform addresses data exchange rather than outbreak analytics "
         "(Zuniga et al., 2026). Digitization has produced data that local units still analyze "
         "by hand.")
add_para(doc, "The second theme, spatial analysis that stops at description, shows that "
         "spatio-temporal methods for dengue are mature (Rotejanaprasert et al., 2024; Sena et "
         "al., 2025) and that Philippine hotspots are persistent at the regional level yet "
         "unstable at the barangay level (Olana, Thongprachum, et al., 2025; Medina et al., "
         "2023). These studies, however, are retrospective and aggregate cases to administrative "
         "units, and their authors call for finer, area-based surveillance (Olana et al., 2026). "
         "None implements the case-address rule of three or more cases within 200 meters within "
         "four weeks that city surveillance units apply manually.")
add_para(doc, "The third theme, alerts that do not reach responders in time, shows that "
         "threshold-based early warning is well validated (Thayer et al., 2025; Cardenas et al., "
         "2022), but that notification and response delays concentrate at the municipal and "
         "district level (Bochner et al., 2023) and that integration of alerting tools into "
         "routine surveillance platforms remains rare (Sanchez Tejeda et al., 2023). Low-cost SMS "
         "and email channels can close part of this gap (Franklin et al., 2025; Schneider et al., "
         "2025).")
add_para(doc, "The fourth theme, decision support without a resource recommender, shows that "
         "hotspot detection is justified as an input to resource allocation (Osako et al., 2026) "
         "and that spatial decision support improves the deployment of vector-control resources "
         "(García et al., 2022). No reviewed study, however, translates detected dengue hotspots "
         "into explicit recommendations of medicines, personnel, and supplies for a city health "
         "unit, and because evidence for any single vector-control method remains limited (Low "
         "et al., 2025; Saadatian-Elahi et al., 2025), a transparent, rule-based recommender that "
         "supports the judgment of epidemiologists is the defensible design.")
add_para(doc, "The fifth theme, constraints that make integration urgent, shows that Philippine "
         "local health units face restrictive hiring, personnel budget caps, and workforce "
         "migration (Pepito et al., 2025), fragmented coordination under devolution (de Claro et "
         "al., 2024), and delayed budget transfers (Ravishankar et al., 2024), while ransomware "
         "increasingly disrupts health information systems (Neprash et al., 2022). These "
         "conditions make automation necessary and make role-based access, audit logging, "
         "encryption, and secure backups requirements rather than options under the Data Privacy "
         "Act of 2012.")

add_section(doc, "", "Synthesis")
add_para(doc, "Taken together, the literature provides credible evidence for digitized reporting, "
         "spatio-temporal cluster detection, statistical threshold alerting, forecasting with "
         "existing models such as Prophet (Fuad et al., 2026; Chen & Moraga, 2025), decision "
         "support for resource allocation, and low-cost notification, each in isolation. What is "
         "absent is an integrated, city-level system that connects threshold detection under the "
         "PIDSR alert and epidemic thresholds and the CESU five-year average, case-address "
         "spatio-temporal hotspot detection, near-term trend forecasting, hotspot-based resource "
         "allocation recommendation, and SMS and email notification within one CESU workflow, "
         "hosted on local government infrastructure and governed by the Data Privacy Act. The "
         "present study addresses this gap for the City Epidemiology and Surveillance Unit of "
         "Parañaque City and evaluates the resulting system with its intended users against "
         "ISO/IEC 25010:2023.")


add_section(doc, "", "Conceptual Framework")

add_para(doc, "The conceptual framework of the study follows an Input-Process-Output model that "
         "structures the development and evaluation of the system. The model maps the knowledge, "
         "software, data, and infrastructure inputs to the iterative development process and to "
         "the resulting outputs. Figure 1 presents the model graphically; the three subsections "
         "that follow enumerate the constituent items of each block.",
         first_line_indent=0)

add_figure(doc, FIG_DIR + r"\fig01_ipo.png",
           "Figure 1. Conceptual Model of the Study",
           width_inches=6.2,
           note="The dashed arrow represents the iterative refinement loop "
                "in which testing and evaluation feedback informs subsequent development cycles.")

add_section(doc, "2.4.1", "Input")
add_lettered(doc, "a", "Knowledge Requirements: the PIDSR alert and epidemic threshold method "
           "(DOH, 2014) and the historical limits method (Stroup et al., 1989); "
           "the CESU spatio-temporal cluster rule; the DBSCAN clustering algorithm (Ester et al., "
           "1996); the Prophet forecasting model (Taylor & Letham, 2018); the outbreak response "
           "protocol of the CESU and applicable DOH guidelines; the ISO/IEC 25010:2023 product quality "
           "model (ISO/IEC, 2023); and Republic Act No. 10173 (2012) with its implementing circulars.")
add_lettered(doc, "b", "Software Requirements: PHP 7.4 with the Laravel 8 framework; MySQL 8; "
           "Python 3.8 with FastAPI, scikit-learn, and Prophet; React, Leaflet.js, Chart.js, and "
           "Tailwind CSS; an SMS gateway and the City Government email service.")
add_lettered(doc, "c", "Data Requirements: the Parañaque City PIDSR Registry export covering 2010 "
           "to 2026 with approximately 35,000 patient-level case records across 29 diseases and 16 "
           "barangays; barangay population figures; OpenStreetMap base tiles and barangay "
           "boundaries.")
add_lettered(doc, "d", "Infrastructure Requirements: the DICT-provisioned server hosting the HRMO "
           "portal and its authentication service.")

add_section(doc, "2.4.2", "Process")
add_lettered(doc, "a", "Requirements analysis through structured consultation with CESU personnel "
           "on the surveillance and outbreak response workflow.")
add_lettered(doc, "b", "System design covering use case analysis, the database schema, the layered "
           "architecture, and the recommendation and notification rules.")
add_lettered(doc, "c", "Iterative development of the nine modules using Agile-inspired "
           "prototyping.")
add_lettered(doc, "d", "Testing through documented test cases with measurable pass criteria and "
           "reconciliation against the CESU PIDSR workbook.")
add_lettered(doc, "e", "Institutional authorization, informed consent, evaluation using the ISO/IEC "
           "25010-based instrument, and validation of system outputs by CESU personnel.")

add_section(doc, "2.4.3", "Output")
add_lettered(doc, "a", "A Web-Based Disease Outbreak Management System for the City Epidemiology "
           "and Surveillance Unit, deployed on the existing DICT-provisioned server.")
add_lettered(doc, "b", "Documented test results for each module.")
add_lettered(doc, "c", "ISO/IEC 25010:2023 evaluation results and CESU output validation results, "
           "documenting acceptance against the threshold weighted mean of 3.41.")
add_lettered(doc, "d", "Technical documentation and turnover of the system to the City Health "
           "Office Health Information Management Unit.")

add_section(doc, "", "Operational Definition of Terms")

terms = [
    ("Audit Log.",
     "An append-only record in the system database capturing user actions, including authentication events, data writes, exports, rule changes, and notifications, in support of Republic Act No. 10173 (2012) accountability requirements."),
    ("CESU.",
     "City Epidemiology and Surveillance Unit, a unit of the City Health Office of Parañaque City responsible for disease surveillance, weekly PIDSR reporting, outbreak investigation, and recommendation of public health interventions within the city. Only CESU personnel can log in to the system."),
    ("CESU Five-Year Average.",
     "The cumulative mean number of cases for a disease up to a given morbidity week across the five preceding years, used by the CESU in its PIDSR workbook as the reference for unusual increases."),
    ("Data Encoder.",
     "A system user role with permission to encode and import case records and to view and export only the user's personal data-entry log."),
    ("DBSCAN.",
     "Density-Based Spatial Clustering of Applications with Noise, an existing clustering algorithm (Ester et al., 1996) that groups points lying within a set distance of each other when a minimum number of points is reached; used in the system to apply the CESU cluster rule."),
    ("Alert Threshold.",
     "A reference value defined in the PIDSR Manual of Procedures as the average case count for the same morbidity week over the past three to five years plus one standard deviation (DOH, 2014, p. 57); the system uses a five-year baseline."),
    ("Epidemic Threshold.",
     "A reference value defined in the PIDSR Manual of Procedures as the same average plus two standard deviations (DOH, 2014, p. 57), a form of the historical limits method (Stroup et al., 1989). The system raises an alert condition when the current week's count exceeds this value, or when a single case of a disease designated for case-based triggers is reported."),
    ("Health Analyst.",
     "A system user role, typically a CESU epidemiologist or surveillance officer, with permission to view maps, thresholds, hotspots, forecasts, risk tiers, and recommendations, to record actions taken, and to generate reports."),
    ("Hotspot.",
     "A spatio-temporal cluster of three or more cases of the same disease occurring within 200 meters of each other within a four-week period, following the CESU cluster rule."),
    ("HRMO Portal Authentication.",
     "The authentication mechanism of the Parañaque City HRMO portal, used by the system to verify that the requesting user is an active city government employee. Passing HRMO authentication is necessary but not sufficient; the user must also be CESU personnel with a role assigned in the system."),
    ("ISO/IEC 25010.",
     "The international product quality model jointly published by the International Organization for Standardization and the International Electrotechnical Commission (ISO/IEC, 2023), which superseded the 2011 edition, used in this study as the evaluation framework of the system."),
    ("Notification.",
     "An SMS or email message sent by the system to designated personnel when a threshold exceedance or a new hotspot is detected, containing no patient identifiers."),
    ("PIDSR.",
     "The Philippine Integrated Disease Surveillance and Response framework, the national disease notification system implemented by the Department of Health (DOH, 2014)."),
    ("Prophet.",
     "An existing open-source time-series forecasting model developed by Meta (Taylor & Letham, 2018), used with yearly seasonality and without tuning to present probable case trends for the next four morbidity weeks."),
    ("Mean Absolute Percentage Error (MAPE).",
     "The average difference between forecast and reported weekly counts, expressed as a percentage of the reported count; the system adds one to the reported count so that weeks with no cases can be included. Lower values indicate a more accurate forecast."),
    ("Same-Week-Last-Year Comparison.",
     "A simple reference forecast, also called the seasonal-naive forecast, that predicts each week's count as the count reported in the same week of the previous year; a Prophet forecast is displayed only when it is more accurate than this comparison."),
    ("Resource Allocation Recommendation.",
     "A list of medicines, diagnostic supplies, response teams, and information materials that the system recommends for a barangay classified as Moderate or High risk, generated from an Administrator-maintained rule table according to the disease and risk tier."),
    ("Risk Tier.",
     "The rule-based classification of a barangay for a given disease and week as High (above the epidemic threshold and with an active hotspot), Moderate (above the threshold, with an active hotspot, or with a rising forecast trend), or Low (none of these conditions)."),
    ("Role-Based Access Control.",
     "A security model that restricts each user to the functions and data appropriate to the assigned role of Data Encoder, Health Analyst, or Administrator."),
]
terms.append(("Administrator.",
              "A system user role, assigned to designated CESU personnel, with permission to manage the CESU staff authorization list and roles, the resource allocation rule table, notification recipients, and encrypted backups, and to export the full case registry."))
terms.sort(key=lambda t: t[0].lower())  # definitions appear in alphabetical order
for term, desc in terms:
    p = doc.add_paragraph()
    p.paragraph_format.first_line_indent = Inches(0.5)
    set_double_spacing(p)
    r = p.add_run(term + " ")
    r.bold = True
    r.font.name = "Times New Roman"
    r.font.size = Pt(12)
    r2 = p.add_run(desc)
    r2.font.name = "Times New Roman"
    r2.font.size = Pt(12)

# =================================================================
#                     CHAPTER 3
# =================================================================
add_chapter_break(doc, "Chapter 3", "METHODOLOGY")

add_para(doc, "This chapter presents the methods used in the conduct of the study. It "
         "describes the research design, the development of the system, the instruments and "
         "techniques used for testing and evaluation, the processing and statistical treatment "
         "of data, and the schedule of activities.")

add_section(doc, "3.1", "Research Design")
add_para(doc, "This study employs design and development research, which is appropriate for "
         "projects that produce a functional technological artifact and subject it to systematic "
         "evaluation (Richey & Klein, 2007). The study is structured around the design, "
         "development, testing, and evaluation of a Web-Based Disease Outbreak Management System "
         "situated within the operational context of the Parañaque City Epidemiology and "
         "Surveillance Unit (CESU) and the 16 barangays under its jurisdiction. Consistent with "
         "the aim of the Master in Information Technology program of using IT to provide "
         "solutions to problems of organizations and society (CHED, 2010), the research "
         "contribution is the deployable "
         "system itself, together with the testing evidence and the ISO/IEC 25010:2023 (ISO/IEC, 2023) "
         "quality evaluation gathered from CESU personnel and information technology "
         "professionals.")
add_para(doc, "The analytical functions of the system are built from existing and established "
         "methods rather than from newly developed models. The study integrates four bodies of "
         "practice. First, it applies Geographic Information Systems (GIS) principles for the "
         "spatial display of barangay-level disease distributions (Nykiforuk & Flaman, 2011; "
         "Lawson, 2018). Second, it applies the alert and epidemic thresholds prescribed by the "
         "PIDSR Manual of Procedures (DOH, 2014), which follow the historical limits method of "
         "aberration detection (Stroup et al., 1989), alongside the five-year-average comparison "
         "currently practiced by the CESU. Third, it applies the density-based DBSCAN "
         "clustering algorithm (Ester et al., 1996) to implement the CESU spatio-temporal cluster "
         "rule. Fourth, it uses the open-source Prophet forecasting model (Taylor & Letham, 2018) "
         "in its standard configuration to present probable near-term trends. These methods are "
         "connected by transparent, rule-based logic for risk prioritization, resource allocation "
         "recommendation, and notification, coordinated through a single authenticated web "
         "interface integrated with the existing HRMO portal.")
add_para(doc, "An Agile-Inspired Iterative Prototyping Model was adopted to support incremental "
         "development and continuous refinement (Beck et al., 2001). This approach suits a system "
         "that combines data pipelines, spatial analysis, and user-facing dashboards, where "
         "data-quality observations and feedback from CESU personnel call for frequent review "
         "cycles. Each development iteration undergoes internal testing before advancement to the "
         "next, ensuring that data fidelity, functional correctness, and user-interface quality "
         "are maintained throughout.")
add_para(doc, "The study proceeds in five phases:")
add_numbered(doc, 1, "Requirements Analysis. The PIDSR Registry export is audited, and the CESU is "
             "consulted on its surveillance and outbreak response workflow, including how "
             "hotspots are investigated and how medicines, personnel, and supplies are deployed. "
             "Related literature is reviewed, and system features and use cases are specified.")
add_numbered(doc, 2, "System Design. The conceptual model, use cases, relational database schema, "
             "layered web architecture, and resource allocation and notification rules are "
             "designed.")
add_numbered(doc, 3, "Development. The nine modules described under System Modules and the data "
             "preparation pipeline for the PIDSR Registry are implemented iteratively.")
add_numbered(doc, 4, "Testing. Documented test cases are executed against measurable pass "
             "criteria, and system outputs are reconciled against the CESU PIDSR "
             "five-year-average workbook.")
add_numbered(doc, 5, "Evaluation. Institutional authorization and informed consent are secured; "
             "the ISO/IEC 25010:2023-based instrument and the output validation questionnaire "
             "are administered to CESU personnel and IT professionals; and the responses are "
             "analyzed statistically.")

add_section(doc, "3.2", "Research Project Development")
add_section(doc, "3.2.1", "System Overview")
add_para(doc, "The system is conceived as a single integrated web application that consolidates "
         "the outbreak management workflow of the CESU into one authenticated dashboard. It "
         "serves only the authorized personnel of the CESU, a unit of the City Health Office, "
         "through a browser-based interface deployed under the domain of the HRMO portal. "
         "Through the system, authorized CESU personnel can:")
add_lettered(doc, "a", "Log in using their existing HRMO portal account, with the system "
             "verifying that the employee is active in the HRMO database and is listed as "
             "authorized CESU personnel with an assigned role; all other employees are denied.")
add_lettered(doc, "b", "Encode PIDSR-aligned case records through a structured form or import "
             "historical case data through a CSV template.")
add_lettered(doc, "c", "View barangay-level maps of case counts and incidence, threshold status, "
             "active hotspots, and risk tiers for each disease.")
add_lettered(doc, "d", "Monitor weekly disease trends against the PIDSR alert and epidemic thresholds and the "
             "CESU five-year average, with automatically flagged alert conditions.")
add_lettered(doc, "e", "Review spatio-temporal hotspots detected under the CESU cluster rule, "
             "including clusters that span barangay boundaries.")
add_lettered(doc, "f", "View probable near-term case trends generated by the Prophet model.")
add_lettered(doc, "g", "Review recommended deployments of medicines, personnel, and supplies "
             "for Moderate and High risk barangays and record the action taken.")
add_lettered(doc, "h", "Receive SMS and email notifications when an alert condition is detected.")
add_lettered(doc, "i", "Generate the weekly PIDSR surveillance report and outbreak memoranda, and "
             "export data according to their role.")
add_lettered(doc, "j", "Administer user roles, review audit logs, and manage encrypted backups.")

add_section(doc, "3.2.2", "Use Case Analysis")
add_para(doc, "Use case analysis was performed to identify the actors who interact with the "
         "system and the functions each actor performs. Five actors were identified. The three "
         "human actors are all CESU personnel, since only authorized CESU staff can log in. The "
         "Data Encoder encodes and imports case records. The Health Analyst, typically a CESU "
         "epidemiologist or surveillance officer, monitors thresholds, hotspots, forecasts, and "
         "recommendations, and generates reports. The Administrator manages users, roles, "
         "recommendation rules, notification recipients, and backups. The HRMO Portal is an "
         "external system actor that authenticates employees, and the Notification Gateway is an "
         "external system actor that delivers SMS and email messages. Figure 2 presents the use "
         "case diagram, in which the «include» relationship denotes behavior that is always "
         "performed as part of the base use case, and the «extend» relationship denotes optional "
         "behavior that occurs only when a stated condition is met. Table 3 summarizes the use "
         "cases and their relationships.")
add_figure(doc, FIG_DIR + r"\fig03_use_case.png",
           "Figure 2. Use Case Diagram of the System",
           width_inches=6.2,
           note="Every use case includes Log In through the HRMO Portal; this relationship is "
                "drawn once for readability.")
add_table(doc, 3, "Use Cases, Actors, and Relationships",
          ["Use Case", "Primary Actor", "Description", "Relationship"],
          [
              ("Log In", "All users; HRMO Portal",
               "Authenticate through the HRMO portal, verify active employment, and confirm "
               "authorized CESU personnel with an assigned role.",
               "Included by all use cases"),
              ("Encode Case Record", "Data Encoder",
               "Enter a PIDSR-aligned case record.",
               "«include» Validate Record; «include» Write Audit Log"),
              ("Import Case Records", "Data Encoder",
               "Upload historical records using a CSV template.",
               "«extend» Encode Case Record (bulk entry)"),
              ("Monitor Epidemic Thresholds", "Health Analyst",
               "Compare weekly counts with the PIDSR alert and epidemic thresholds and the CESU "
               "five-year average.",
               "«include» Compute Thresholds"),
              ("Detect Hotspots", "Health Analyst",
               "Identify clusters of three or more cases within 200 m and four weeks.",
               "«include» Locate Case Addresses"),
              ("View Trend Forecast", "Health Analyst",
               "Display the probable near-term trend from the Prophet model.",
               "None"),
              ("Prioritize Barangays and Recommend Resources", "Health Analyst",
               "Assign High, Moderate, or Low risk tiers by rule and recommend medicines, "
               "personnel, and supplies for Moderate and High risk barangays.",
               "«include» Monitor Epidemic Thresholds; «include» Detect Hotspots"),
              ("Send Outbreak Notification", "Notification Gateway",
               "Send SMS and email to designated recipients.",
               "«extend» Monitor Epidemic Thresholds and Detect Hotspots (when an alert "
               "condition is met)"),
              ("Generate Surveillance Report", "Health Analyst",
               "Produce the weekly PIDSR report and outbreak memorandum.",
               "«include» Write Audit Log"),
              ("Export Data", "Health Analyst; Administrator",
               "Export role-tiered data files.",
               "«extend» Generate Surveillance Report; «include» Write Audit Log"),
              ("Manage Users and Rules", "Administrator",
               "Assign roles; maintain recommendation rules and notification recipients.",
               "«include» Write Audit Log"),
              ("Manage Backups", "Administrator",
               "Create, verify, and restore encrypted backups.",
               "Extended by Restore Backup (when recovery is needed)"),
          ],
          widths=[1.35, 1.2, 2.35, 1.6])

add_section(doc, "3.2.3", "System Modules")

add_heading(doc, "Module 1: Case Data Management", level=3, align=WD_ALIGN_PARAGRAPH.LEFT)
add_para(doc, "This module provides a structured web-based interface for encoding PIDSR disease "
         "case records into the MySQL database. Input fields mirror the PIDSR case report form, "
         "consistent with DOH (2014) reporting standards, including disease name, case "
         "classification, date of onset, date of admission, patient barangay, patient street and "
         "purok address, reporting health facility, age, sex, vaccination history, and case "
         "outcome. Input validation checks completeness and classification consistency before "
         "record insertion. A batch import function supports CSV upload of multiple records using "
         "a PIDSR-compatible template, facilitating transfer of historical data from existing "
         "spreadsheet-based surveillance records. Every insertion and update is written to the "
         "audit log.")

add_heading(doc, "Module 2: Disease Mapping", level=3, align=WD_ALIGN_PARAGRAPH.LEFT)
add_para(doc, "This module renders an interactive map of the 16 Parañaque barangays using "
         "Leaflet.js with OpenStreetMap tiles. Overlaid layers include a barangay choropleth "
         "colored by case rate per 10,000 population, case-count circles, the threshold status "
         "of each barangay, active hotspot boundaries, and the risk tier of each barangay. Layers "
         "are independently toggleable, allowing health officials to focus on the spatial pattern "
         "most relevant to the surveillance question at hand. Maps operate on aggregated counts "
         "and cluster outlines and do not display individual patient identifiers.")

add_heading(doc, "Module 3: Epidemic Threshold Monitoring", level=3,
            align=WD_ALIGN_PARAGRAPH.LEFT)
add_para(doc, "This module renders weekly case-count trend charts via Chart.js with overlays for "
         "the CESU five-year average and the two thresholds prescribed by the PIDSR Manual of "
         "Procedures: the alert threshold, computed as the average for the same morbidity week "
         "over the past five years plus one standard deviation, and the epidemic threshold, "
         "computed as that average plus two standard deviations (DOH, 2014, p. 57), following "
         "the historical limits method (Stroup et al., 1989). Each week's case count is marked as "
         "below the alert threshold, at the alert level, or above the epidemic threshold. For "
         "diseases that the manual designates for case-based triggers, such as measles and "
         "acute flaccid paralysis, a single case raises an alert regardless of the average "
         "(DOH, 2014, p. 58). Thresholds are pre-computed by a scheduled Python job and stored "
         "in a thresholds table for fast dashboard rendering.")

add_heading(doc, "Module 4: Spatio-Temporal Hotspot Detection", level=3,
            align=WD_ALIGN_PARAGRAPH.LEFT)
add_para(doc, "This module implements the CESU cluster rule, under which three or more cases "
         "occurring within 200 meters of each other within a four-week period constitute a "
         "cluster requiring investigation. Case addresses are first converted into geographic "
         "coordinates through a cached geocoding pipeline that queries the OpenStreetMap "
         "Nominatim service with progressively broader address components and records the "
         "precision of each result; only cases located at street level or better are clustered. "
         "For each four-week window, the existing DBSCAN algorithm (Ester et al., 1996) is "
         "applied with a neighborhood radius of 200 meters, computed with the haversine "
         "distance, and a minimum of three cases. Each detected cluster is stored with its member "
         "cases, center, date range, and the barangays it spans, so that clusters crossing "
         "barangay boundaries remain visible. A new cluster raises an alert condition.")

add_heading(doc, "Module 5: Disease Trend Forecasting", level=3, align=WD_ALIGN_PARAGRAPH.LEFT)
add_para(doc, "This module presents probable near-term case trends using the existing open-source "
         "Prophet model (Taylor & Letham, 2018) with yearly seasonality, applied in multiplicative "
         "form so that the seasonal peak scales with the level of the series. For each supported "
         "disease, the model is fitted to the weekly counts of Confirmed and Probable cases from "
         "2010 to 2025, the same case definition used for the PIDSR thresholds, and produces a "
         "trend for the four morbidity weeks after the current week with an 80 percent "
         "uncertainty interval. The years 2020 and 2021, when COVID-19 restrictions suppressed "
         "PIDSR reporting, remain in the series and are treated as a limitation of the forecast. "
         "Because Prophet does not perform well on every disease (Olana, Poprom, et al., 2025; "
         "Fuller et al., 2025), the forecast is displayed only for diseases for which it "
         "outperforms a simple same-week-last-year comparison on data withheld from the model. "
         "For this check, the model is fitted to 2010 to 2023, asked to predict every week of 2024 "
         "and 2025, and compared with the reported counts. The check is an operational safeguard rather than "
         "model development. The study does not involve model development or tuning, and the "
         "forecast is presented to users as a probable trend rather than a prediction of an "
         "exact outbreak.")

add_heading(doc, "Module 6: Risk Prioritization and Resource Allocation Recommendation", level=3,
            align=WD_ALIGN_PARAGRAPH.LEFT)
add_para(doc, "This module classifies each barangay, for a selected disease and morbidity week, "
         "into a risk tier using transparent rules. A barangay is classified as High when its "
         "weekly count exceeds the epidemic threshold and it contains an active hotspot; as "
         "Moderate when it exceeds the threshold, contains an active hotspot, or shows a rising "
         "forecast trend; and as Low otherwise. A rising forecast trend means that the forecast "
         "for the fourth week ahead is at least 10 percent and at least one case higher than the "
         "forecast for the first week ahead. Because forecasts begin from the present, the trend "
         "is considered only when the selected week is the current morbidity week, and only for "
         "diseases whose forecasts are displayed. The rules are deliberately simple so that CESU "
         "personnel can verify every classification.")
add_para(doc, "For High and Moderate barangays, a knowledge-based recommender produces a list of "
         "recommended resources drawn from a recommendation rule table maintained by the "
         "Administrator. Each rule specifies, for a disease and risk tier, a recommended response "
         "team, diagnostic or other supply, medicine, or information material, together with a "
         "scaling basis: a fixed quantity, a quantity per active case in the last four weeks, a "
         "quantity per 1,000 residents, or a quantity assessed by CESU personnel. Rules for the "
         "Moderate tier apply to both Moderate and High barangays, rules for the High tier add "
         "escalation measures such as vector control in the hotspot area, and a disease without "
         "rules of its own receives general case verification and reporting rules. The initial "
         "rule table is encoded from published response guidance, namely the outbreak "
         "investigation and response procedures of the PIDSR Manual of Procedures (DOH, 2014), "
         "the 4S strategy of the Department of Health against dengue, and the dengue guidelines "
         "of the World Health Organization (WHO, 2009), together with WHO standards for measles "
         "and acute flaccid paralysis. Each rule is then validated with CESU personnel, and "
         "until a rule is validated the system labels the recommendations based on it as drafts. "
         "Following evidence that decision models agree more on the ranking of interventions "
         "than on their magnitude (Shea et al., 2023), recommendations are ranked by risk tier "
         "and case count, and the Health Analyst records whether each recommendation was acted "
         "upon, creating an auditable record of resource deployment decisions. Every change to "
         "the rule table is recorded in the audit log, and an edited rule returns to draft "
         "status until it is validated again.")

add_heading(doc, "Module 7: Outbreak Alerts and Notifications", level=3,
            align=WD_ALIGN_PARAGRAPH.LEFT)
add_para(doc, "This module sends SMS and email notifications to recipients designated by the "
         "Administrator, such as the CESU head, surveillance officers, and the City Health "
         "Officer, whenever a threshold exceedance or a new hotspot is detected. SMS messages are "
         "sent through an SMS gateway and emails through the email service of the City "
         "Government. To prevent alert fatigue, at most one notification is sent per disease, "
         "barangay, alert type, and morbidity week. Messages state the disease, barangay, alert "
         "type, and a link to the dashboard, and contain no patient identifiers. Every "
         "notification and its delivery status are recorded in a notification log.")

add_heading(doc, "Module 8: Surveillance Reports and Data Export", level=3,
            align=WD_ALIGN_PARAGRAPH.LEFT)
add_para(doc, "This module generates the weekly PIDSR surveillance report in the format of the "
         "CESU workbook, including summary tables by disease, cases by barangay with rates per "
         "10,000 population, and an auto-generated outbreak memorandum. It also provides "
         "role-tiered CSV exports: Data Encoders can export only their personal data-entry log, "
         "Health Analysts can export summary reports aggregated by week, disease, and barangay, "
         "and Administrators can export the full case registry. All exports are recorded in the "
         "audit log in support of the security requirements of Republic Act No. 10173 (2012, "
         "Sec. 20).")

add_heading(doc, "Module 9: Security and System Administration", level=3,
            align=WD_ALIGN_PARAGRAPH.LEFT)
add_para(doc, "This module provides the security controls recommended for health information "
         "systems that process personal and sensitive personal information. Role-based access "
         "control restricts each user to the functions and data appropriate to the Data Encoder, "
         "Health Analyst, or Administrator role, and accounts with access to patient-level "
         "records require multi-factor authentication. An append-only audit log records "
         "authentication events, data writes, exports, rule changes, and notification events "
         "(Kannampallil & Adler-Milstein, 2022). Data in transit is encrypted through HTTPS. "
         "Because ransomware most often disrupts health services through system downtime "
         "(Neprash et al., 2022), automated daily database backups are encrypted with AES-256 "
         "before storage, retained according to a defined schedule, and verified through "
         "periodic test restorations, and a documented restoration procedure supports recovery "
         "after failure. These measures implement the organizational, physical, and technical "
         "security measures required by Republic Act No. 10173 (2012, Sec. 20) and the National "
         "Privacy Commission (NPC, 2023), and a breach response procedure supports notification "
         "of the Commission and affected data subjects within 72 hours (NPC, 2016).")

add_section(doc, "3.2.4", "Python Analytics Service")
add_para(doc, "The analytical functions run as a Python 3.8 FastAPI application on the same "
         "DICT server as the Laravel web application. The service listens only on the loopback "
         "interface and is not exposed to the public internet. It exposes endpoints for "
         "retrieving trend forecasts and for triggering hotspot detection, while scheduled jobs "
         "compute thresholds, geocode new case addresses, and refresh hotspots after each data "
         "update. FastAPI was selected for its native data validation and automatic API "
         "documentation. The Laravel application invokes the service through internal HTTP calls.")

add_section(doc, "3.2.5", "Development Environment")

add_heading(doc, "Server-Side Technologies", level=3, align=WD_ALIGN_PARAGRAPH.LEFT)
add_lettered(doc, "a", "PHP 7.4 with the Laravel 8 framework, serving the web application and "
           "exposing JSON API endpoints to the frontend, matched to the runtime of the existing "
           "Parañaque LGU production server on Ubuntu 20.04.")
add_lettered(doc, "b", "MySQL 8, hosting the system database and accessed by both the Laravel "
           "application and the Python analytics service.")
add_lettered(doc, "c", "Python 3.8 with FastAPI and uvicorn, hosting the analytics service.")
add_lettered(doc, "d", "scikit-learn for the DBSCAN clustering algorithm and Prophet (Meta) for "
           "trend forecasting, both used as existing libraries.")
add_lettered(doc, "e", "An SMS gateway and the City Government email service (SMTP) for "
           "notifications.")
add_lettered(doc, "f", "mysqldump and OpenSSL AES-256 encryption for automated encrypted backups.")
add_heading(doc, "Client-Side Technologies", level=3, align=WD_ALIGN_PARAGRAPH.LEFT)
add_lettered(doc, "a", "React 19 single-page application served as a static bundle by the Laravel "
           "application.")
add_lettered(doc, "b", "Leaflet.js and react-leaflet for interactive web mapping; Chart.js and "
           "react-chartjs-2 for trend visualizations.")
add_lettered(doc, "c", "Tailwind CSS for responsive layout and dashboard styling.")
add_heading(doc, "Data Sources", level=3, align=WD_ALIGN_PARAGRAPH.LEFT)
add_lettered(doc, "a", "Parañaque City PIDSR Registry export covering 2010 to 2026, approximately "
           "35,000 patient-level case records.")
add_lettered(doc, "b", "OpenStreetMap tile services, the Nominatim geocoding service, and barangay "
           "polygon GeoJSON from open Philippine GIS data providers.")
add_lettered(doc, "c", "Barangay population figures (2024 projection, 723,860 city total) for "
           "computing case rates.")

add_section(doc, "3.2.6", "System Architecture")
add_para(doc, "The system follows a four-layer architecture comprising the Presentation, "
         "Application Logic, Analytics Service, and Data layers. The Presentation Layer is a "
         "React 19 single-page application with Leaflet.js map panels, Chart.js charts, and "
         "Tailwind CSS dashboard components. The Application Logic Layer is implemented in "
         "Laravel 8 and handles HRMO authentication, role checks, query orchestration, risk "
         "tiering, resource recommendation, notification dispatch through the SMS gateway and "
         "email service, audit logging, and internal calls to the analytics service. The "
         "Analytics Service Layer is a Python FastAPI process bound to localhost that performs "
         "threshold computation, geocoding, hotspot detection, and forecasting. The Data Layer "
         "is MySQL hosted on the DICT-provisioned server, with encrypted backups stored "
         "separately.")
add_para(doc, "All authentication, authorization, and validation are enforced at the Laravel "
         "HTTP boundary. Because the analytics service accepts connections only from the same "
         "host, unauthenticated network traffic cannot reach it. Figure 3 summarizes the "
         "architecture and the request and response flows between layers.")
add_figure(doc, FIG_DIR + r"\fig02_architecture.png",
           "Figure 3. System Architecture",
           width_inches=6.0,
           note="The analytics service is bound to localhost and is not internet-facing.")

add_section(doc, "3.2.7", "Operational Flow")
add_para(doc, "The system supports the outbreak management cycle of the CESU through five linked "
         "stages, namely detect, locate, prioritize, recommend, and notify, as illustrated in "
         "Figure 4. The operational flow proceeds as follows:")
add_figure(doc, FIG_DIR + r"\fig04_outbreak_flow.png",
           "Figure 4. Outbreak Management Flow of the System",
           width_inches=6.0)
add_numbered(doc, 1, "A CESU staff member opens the system from a supported web browser and is "
             "authenticated through the HRMO portal; Laravel verifies active employment, confirms "
             "that the employee is authorized CESU personnel with an assigned role, and attaches "
             "the role to the request. Employees who are not authorized CESU personnel are "
             "denied, and the denied attempt is written to the audit log.")
add_numbered(doc, 2, "A Data Encoder encodes or imports case records; each record is validated, "
             "stored, and written to the audit log.")
add_numbered(doc, 3, "Scheduled jobs geocode new case addresses, update thresholds, and run "
             "hotspot detection for the current four-week window.")
add_numbered(doc, 4, "When a weekly count exceeds the epidemic threshold or a new hotspot is "
             "detected, the system raises an alert condition.")
add_numbered(doc, 5, "The system assigns risk tiers to the affected barangays and generates "
             "resource allocation recommendations from the rule table.")
add_numbered(doc, 6, "Designated recipients are notified through SMS and email, and the "
             "notification is logged.")
add_numbered(doc, 7, "The Health Analyst reviews the alert on the dashboard and map, records the "
             "action taken on each recommendation, and generates the weekly surveillance report "
             "or outbreak memorandum.")

add_section(doc, "3.2.8", "Database Design")
add_para(doc, "The MySQL database is hosted on the DICT-provisioned server. The schema follows "
         "third-normal-form principles, with reference tables for diseases, barangays, and "
         "facilities; a transactional cases table for the PIDSR case registry; and analytical, "
         "notification, and security tables. The principal tables are:")

tables_info = [
    ("cases",
     "PIDSR-aligned line-list table containing approximately 35,000 patient-level records spanning 2010 to 2026, with foreign keys to diseases, barangays, and facilities."),
    ("diseases",
     "Reference table of the 29 notifiable diseases monitored by the system (28 PIDSR priority diseases plus COVID-19), with flags indicating which diseases are enabled for threshold alerting and forecasting."),
    ("barangays",
     "Reference table of the 16 Parañaque barangays with centroid coordinates and population from the 2024 projection (total 723,860 residents)."),
    ("facilities",
     "Reference table of 233 disease reporting units seeded from the PIDSR Registry workbook, flagged as CESU-designated sentinel sites where applicable (29 of 233 facilities)."),
    ("thresholds",
     "Pre-computed per-week reference values for each alert-enabled disease, storing the PIDSR alert threshold (mean plus one standard deviation), the epidemic threshold (mean plus two standard deviations), and the CESU five-year average, together with a flag for diseases that use single-case triggers."),
    ("case_addresses and geocode_cache",
     "Geographic coordinates of case addresses with their geocoding precision, and a cache of geocoding results that avoids repeated queries to the geocoding service."),
    ("detection_runs, case_clusters, and case_cluster_members",
     "Records of each hotspot detection run with its parameters, the clusters detected with their centers, date ranges, and spanned barangays, and the cases belonging to each cluster."),
    ("ai_predictions",
     "Cache table storing recent Prophet trend forecasts indexed by disease and morbidity week."),
    ("recommendation_rules and recommendations",
     "The Administrator-maintained rule table that maps a disease and risk tier to recommended resources and a scaling basis, and the recommendations generated for each barangay and week together with the action recorded by the Health Analyst."),
    ("notification_recipients and notification_log",
     "Designated recipients with their channels and alert subscriptions, and a log of every notification sent with its delivery status."),
    ("user_roles",
     "The CESU staff authorization list, mapping each authorized CESU staff member's HRMO employee identifier to one of three roles: Data Encoder, Health Analyst, or Administrator. An employee without an entry in this table cannot log in."),
    ("audit_log",
     "Append-only table recording authentication events, data writes, exports, rule changes, and notification events in support of Republic Act No. 10173 (2012) accountability. It stores action metadata only (timestamp, employee identifier, action type, affected table, affected row, and a short description) and does not duplicate the contents of patient records."),
    ("backup_log",
     "Record of each encrypted backup with its timestamp, file checksum, size, and the result of periodic test restorations."),
    ("excluded_cases",
     "Audit table holding cases that fall outside the 16-barangay surveillance scope, retained for traceability."),
]
for tname, tdesc in tables_info:
    p = doc.add_paragraph()
    p.paragraph_format.first_line_indent = Inches(0.5)
    set_double_spacing(p)
    r = p.add_run(tname + ". ")
    r.bold = True
    r.font.name = "Times New Roman"
    r.font.size = Pt(12)
    r2 = p.add_run(tdesc)
    r2.font.name = "Times New Roman"
    r2.font.size = Pt(12)

add_section(doc, "3.2.9", "Security Considerations")
add_lettered(doc, "a", "CESU-Only Access. Access requires a valid HRMO portal account, a verified "
             "active employment record, and an entry in the CESU staff authorization list "
             "maintained by the Administrator; employees of other offices and of other City "
             "Health Office units are denied even with a valid HRMO account. Accounts with access "
             "to patient-level records require multi-factor authentication.")
add_lettered(doc, "b", "Role-Based Access Control. Three role levels (Data Encoder, Health "
             "Analyst, and Administrator) restrict access to features and data appropriate to "
             "each role.")
add_lettered(doc, "c", "Audit Logging. Authentication events, data writes, exports, rule changes, "
             "and notifications are recorded in an append-only audit log in support of the "
             "security requirements of Republic Act No. 10173 (2012, Sec. 20).")
add_lettered(doc, "d", "Encryption. All external traffic is served over HTTPS using the existing "
             "SSL certificate of the HRMO portal, and backup files are encrypted with AES-256.")
add_lettered(doc, "e", "Secure Backup and Recovery. Automated daily encrypted backups are retained "
             "on a defined schedule, verified through checksums and periodic test restorations, "
             "and supported by a documented restoration procedure.")
add_lettered(doc, "f", "Localhost-Only Analytics Service. The Python analytics service accepts "
             "connections only from the same host and cannot be reached from the network.")
add_lettered(doc, "g", "Data Minimization. Maps, dashboards, and notifications use aggregated "
             "counts and cluster outlines and do not expose individual patient identifiers, "
             "consistent with the proportionality principle of Republic Act No. 10173 (2012, "
             "Sec. 11).")
add_lettered(doc, "h", "Breach Response. A documented breach response procedure designates "
             "responsible personnel and supports notification of the National Privacy Commission "
             "and affected data subjects within 72 hours of knowledge of a personal data breach "
             "(NPC, 2016).")

add_section(doc, "", "Instruments and Techniques Used")
add_para(doc, "Three instruments are used to verify that the system meets its functional and "
         "quality objectives: documented test cases with measurable pass criteria, used for "
         "developer-driven testing of each module; a software evaluation instrument based on "
         "ISO/IEC 25010:2023, used to assess the system with its intended users and with IT "
         "professionals; and an output validation questionnaire, used by CESU personnel as "
         "domain experts to judge whether the outputs of the system agree with their "
         "professional assessment.")

add_section(doc, "", "Software Testing Plan")
add_para(doc, "The system is tested at three levels, where each level is a precondition for "
         "advancing to the next. Level 1, Unit and Functional Testing, verifies the expected "
         "behavior of each module through documented test cases. Each test case records a test "
         "case identifier, the desired output, the test procedure as a numbered sequence of "
         "steps, the observed result, and a pass or fail status. Level 2, Data Fidelity Testing, "
         "reconciles the system's year-to-date case counts and five-year averages against the "
         "existing CESU PIDSR workbook for the most recent morbidity weeks, and verifies hotspot "
         "detection on a test dataset with planted clusters whose correct result is known in "
         "advance. At the same level, the accuracy of the displayed forecasts is checked on "
         "2024 and 2025 weeks withheld from the model, both as a single two-year forecast and as "
         "repeated four-week forecasts that match the dashboard's use. Level 3, Integration and System Testing, exercises the end-to-end flow from "
         "case encoding through threshold evaluation, hotspot detection, risk tiering, "
         "recommendation, and notification. Table 4 lists the measurable parameters and pass "
         "criteria used across the three levels.")
add_table(doc, 4, "Measurable Testing Parameters and Pass Criteria",
          ["Test Area", "Measurable Parameter", "Pass Criterion"],
          [
              ("Case data management", "Rejection of invalid records; audit logging of writes",
               "100% of invalid test records rejected; 100% of valid writes saved and logged"),
              ("Threshold monitoring", "Agreement with independent recomputation and with the "
               "CESU workbook",
               "Exact match with recomputation; difference within 1% of workbook five-year "
               "averages"),
              ("Hotspot detection", "Detection of planted clusters in the test dataset",
               "100% of planted clusters detected; no spurious clusters; identical results on "
               "repeated runs"),
              ("Trend forecasting", "Response time and repeatability",
               "Forecast returned within 3 seconds; identical values on repeated calls"),
              ("Forecast accuracy", "Mean absolute percentage error (MAPE) on 2024 and 2025 "
               "weeks withheld from the model, compared with the same-week-last-year comparison",
               "Every displayed forecast has a lower MAPE than the comparison; every other "
               "forecast is withheld"),
              ("Risk tiering and recommendation", "Agreement with the rule table",
               "100% of test barangays assigned the tier and recommendations defined by the "
               "rules"),
              ("Notifications", "Delivery time, de-duplication, and content",
               "Delivered within 5 minutes of detection; no duplicate per disease, barangay, "
               "type, and week; no patient identifiers"),
              ("Reports and export", "Agreement of report totals with the database; "
               "role restriction",
               "Totals match database counts; exports limited to the user's role"),
              ("Performance", "Page and map load time on the office network",
               "Dashboard within 3 seconds; map within 5 seconds"),
              ("Security", "Access control, logging, encryption, and recovery",
               "100% of unauthorized requests denied; 100% of sensitive actions logged; HTTPS "
               "enforced; restored backup matches source row counts and checksums"),
          ],
          widths=[1.4, 2.3, 2.8])
add_para(doc, "Any test case that fails its criterion is logged as a defect, corrected, and "
         "re-tested before evaluation begins.")

add_section(doc, "", "Evaluation Instrument")
add_para(doc, "The evaluation instrument (Appendix A) consists of an informed consent form and "
         "four parts. Part I gathers a brief respondent profile: office or unit, position, "
         "respondent group, and years of experience, with the respondent's name optional. Part "
         "II contains 25 indicators rated on a five-point scale under six ISO/IEC 25010:2023 "
         "characteristics: Functional Suitability (four indicators), Performance Efficiency "
         "(four), Interaction Capability (five), Reliability (four), Security (four), and "
         "Maintainability (four, rated by IT professional respondents only). Part III, answered "
         "by CESU and City Health Office personnel only, contains six statements on the "
         "agreement of the system's alerts, hotspots, weekly report figures, trend forecasts, "
         "and resource recommendations with professional judgment and with the existing PIDSR "
         "workbook. Part IV asks open-ended questions on the most useful features, problems "
         "encountered, and suggested improvements.")

add_section(doc, "", "Evaluation Procedure")
add_para(doc, "The developed system is evaluated using a software evaluation instrument anchored "
         "on the ISO/IEC 25010:2023 product quality model (ISO/IEC, 2023), which superseded the "
         "2011 edition. Six of its quality characteristics are assessed through Likert-scaled "
         "indicators adapted from the standard's characteristic definitions:")
add_lettered(doc, "a", "Functional Suitability: the degree to which the system provides functions "
             "that meet stated and implied needs.")
add_lettered(doc, "b", "Performance Efficiency: the degree to which the system performs within "
             "stated time and resource constraints.")
add_lettered(doc, "c", "Interaction Capability, formerly Usability: the degree to which the system "
             "can be used by specified users to achieve specified goals effectively and "
             "efficiently.")
add_lettered(doc, "d", "Reliability: the degree to which the system performs specified functions "
             "under specified conditions for a specified period.")
add_lettered(doc, "e", "Security: the degree to which the system protects information and data so "
             "that persons have access appropriate to their authorization.")
add_lettered(doc, "f", "Maintainability: the degree of effectiveness and efficiency with which the "
             "system can be modified. It is rated by the IT professional respondents only, since "
             "its indicators require technical knowledge of the system's construction.")
add_para(doc, "In addition, as recommended by the panel, the outputs of the system are validated "
         "by CESU and City Health Office personnel as domain experts. A separate output "
         "validation questionnaire asks these respondents to rate their agreement that the "
         "system's alerts, hotspots, weekly report figures, trend forecasts, and resource "
         "recommendations are consistent with their professional assessment and with the "
         "existing PIDSR workbook.")
add_para(doc, "The evaluation procedure is conducted in the following sequence:")
add_numbered(doc, 1, "Twenty-five to thirty respondents are purposively selected from the target "
             "user population, comprising CESU personnel (epidemiologists, surveillance officers, "
             "and data personnel), City Health Office medical officers, and supervising health "
             "workers. Five IT professionals with experience in web systems, government IT, or "
             "health informatics are also selected to evaluate the technical implementation.")
add_numbered(doc, 2, "The written informed consent of each respondent is obtained before "
             "participation.")
add_numbered(doc, 3, "The system, its objectives, and its major functions are demonstrated to the "
             "respondents using a version of the system that contains only anonymized data.")
add_numbered(doc, 4, "Respondents use the system with test accounts and evaluate it individually "
             "using printed forms or Google Forms.")
add_numbered(doc, 5, "The accomplished forms are collected, organized, and tabulated to determine "
             "the weighted mean for each indicator, each quality characteristic, and the "
             "output validation items.")
add_numbered(doc, 6, "The weighted means are interpreted using the adopted scales to determine the "
             "level of acceptability of the system and the level of agreement of domain experts "
             "with its outputs.")

add_section(doc, "", "Ethical Considerations")
add_para(doc, "Because the system processes personal and sensitive personal health information "
         "and the evaluation involves human participants, the study observes the following "
         "ethical safeguards, consistent with Republic Act No. 10173 (2012) and the principles "
         "of the national ethical guidelines for research involving human participants, namely "
         "informed consent, voluntary participation, privacy and confidentiality, and minimal "
         "risk (Philippine Health Research Ethics Board [PHREB], 2022).")
add_lettered(doc, "a", "Ethical Basis of the Study. The Technological University of the "
             "Philippines does not maintain a Research Ethics Committee. In consultation with the "
             "research adviser, the ethical conduct of the study therefore rests on three "
             "safeguards: the written informed consent of every respondent, the institutional "
             "authorization of the City Health Office and the Office of the City Mayor, and a "
             "Non-Disclosure and Data Privacy Agreement between the researcher and the City "
             "Health Office. The study involves minimal risk: respondents are adult "
             "professionals who answer an anonymous questionnaire, and only anonymized data are "
             "shown to them.")
add_lettered(doc, "b", "Institutional Authorization. Access to CESU data is covered by the written "
             "endorsement of the City Health Office and the approval of the City Mayor, and by a "
             "signed and notarized Non-Disclosure and Data Privacy Agreement executed by the "
             "researcher with the City Health Office, which governs the handling, storage, and "
             "return of the data.")
add_lettered(doc, "c", "Informed Consent and Voluntary Participation. Each respondent receives a "
             "written explanation of the purpose, procedure, risks, and benefits of the study and "
             "signs a consent form. Participation is voluntary, and respondents may withdraw at "
             "any time. Because the researcher is an employee of the Human Resource Management "
             "Office, the consent form states explicitly that participation or refusal has no "
             "effect on the respondent's employment, performance rating, or transactions with "
             "the office.")
add_lettered(doc, "d", "Confidentiality of Respondents. Names are optional, responses are reported "
             "only as group averages, and accomplished forms are kept securely and destroyed "
             "after the completion of the study.")
add_lettered(doc, "e", "Protection of Patient Data. Patient records remain within the City Health "
             "Office servers; no physical or electronic copies are taken outside. No live "
             "patient data are used in any test, demonstration, or evaluation version of the "
             "system. The demonstration version uses an anonymized copy of the data in which "
             "street addresses are removed, coordinates are displaced by up to 50 meters, dates "
             "are shifted by up to three days, and ages are grouped, which preserves aggregate "
             "patterns while preventing re-identification.")
add_lettered(doc, "f", "Turnover. Upon completion and successful deployment, full administrative "
             "control of the system and its database is turned over to the City Health Office "
             "Health Information Management Unit.")

add_section(doc, "", "Data Processing and Statistical Treatment of Data")
add_para(doc, "The collected responses are processed through descriptive statistics, with the "
         "weighted mean serving as the primary statistical measure. The weighted mean for each "
         "indicator, each quality characteristic, and each output validation item is computed "
         "using the following formula:")
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
set_double_spacing(p)
r = p.add_run("X̄ = Σfx / N")
r.italic = True
r.font.name = "Times New Roman"
r.font.size = Pt(12)
add_para(doc, "where X-bar is the weighted mean, Σfx is the sum of the products of the frequency "
         "of responses and the corresponding scale value, and N is the total number of responses. "
         "Weighted means are computed separately for the CESU and City Health Office group and "
         "the IT professional group, because the groups differ in size and in the expertise they "
         "bring to the evaluation.")
add_para(doc, "The weighted means for the quality characteristics are interpreted using the "
         "acceptability scale in Table 5, and the output validation items using the agreement "
         "scale in Table 6. The system acceptance criterion is an overall weighted mean of 3.41 "
         "or higher (Moderately Acceptable) among the CESU and City Health Office group, which "
         "constitutes the target user population, and an overall output validation mean of 3.41 "
         "or higher (Agree).")
add_table(doc, 5, "Five-Point Acceptability Scale and Interpretation",
          ["Scale", "Verbal Interpretation", "Range"],
          [("5", "Highly Acceptable", "4.21 – 5.00"),
           ("4", "Moderately Acceptable", "3.41 – 4.20"),
           ("3", "Acceptable", "2.61 – 3.40"),
           ("2", "Fairly Acceptable", "1.81 – 2.60"),
           ("1", "Not Acceptable", "1.00 – 1.80")],
          widths=[0.9, 2.4, 1.6], font_size=11)
add_table(doc, 6, "Five-Point Agreement Scale for Output Validation",
          ["Scale", "Verbal Interpretation", "Range"],
          [("5", "Strongly Agree", "4.21 – 5.00"),
           ("4", "Agree", "3.41 – 4.20"),
           ("3", "Neutral", "2.61 – 3.40"),
           ("2", "Disagree", "1.81 – 2.60"),
           ("1", "Strongly Disagree", "1.00 – 1.80")],
          widths=[0.9, 2.4, 1.6], font_size=11)
add_para(doc, "Responses from the five IT professional respondents are reported as supplementary "
         "validation of the technical implementation rather than as a basis for statistical "
         "inference, given that the group size precludes claims of representativeness.")

add_section(doc, "", "Schedule of Activities")
add_para(doc, "Table 7 presents the schedule of the major activities of the study, from the "
         "securing of institutional authorization to the turnover of the system to the City "
         "Health Office.")
add_table(doc, 7, "Schedule of Activities",
          ["Activity", "Period"],
          [
              ("Securing of institutional authorization from the City Health Office and the "
               "Office of the City Mayor", "July 2023"),
              ("Requirements analysis and consultation with the CESU",
               "2023-2026"),
              ("System design and prototype development", "January to April 2026"),
              ("Proposal defense", "May 2026"),
              ("Revision of Chapters 1 to 3 according to the panel's recommendations; renewed "
               "request for authorization and execution of the Non-Disclosure Agreement",
               "October 2026"),
              ("Development of the alert, hotspot, recommendation, and security modules",
               "November 2026"),
              ("Testing of the system against the measurable pass criteria",
               "November 2026"),
              ("Evaluation and output validation with respondents", "November 2026"),
              ("Data analysis and writing of Chapters 4 and 5", "November 2026"),
              ("Final defense", "November 2026"),
              ("Final revisions and turnover of the system to the City Health Office",
               "November 2026"),
          ],
          widths=[4.3, 1.7], font_size=10)

doc.add_page_break()
# References heading: APA 7 §2.27 — centered, bold, on its own page.
ref_heading = doc.add_paragraph()
ref_heading.alignment = WD_ALIGN_PARAGRAPH.CENTER
ref_heading.paragraph_format.space_before = Pt(0)
ref_heading.paragraph_format.space_after = Pt(0)
set_double_spacing(ref_heading)
_rh = ref_heading.add_run("References")
_rh.bold = True
_rh.font.name = "Times New Roman"
_rh.font.size = Pt(12)

refs = [
    "Abd Naeeim, N. S., & Abdul Rahman, N. (2022). Spatio-temporal clustering analysis using two different scanning windows: A case study of dengue fever in Peninsular Malaysia. *Spatial and Spatio-temporal Epidemiology, 41*, Article 100496. https://doi.org/10.1016/j.sste.2022.100496",
    "Al Ani, M., Garas, G., Hollingshead, J., Cheetham, D., Athanasiou, T., & Patel, V. (2022). Which electronic health record system should we use? A systematic review. *Medical Principles and Practice, 31*(4), 342–351. https://doi.org/10.1159/000525135",
    "Baharom, M., Ahmad, N., Hod, R., & Abdul Manaf, M. R. (2022). Dengue early warning system as outbreak prediction tool: A systematic review. *Risk Management and Healthcare Policy, 15*, 871–886. https://doi.org/10.2147/RMHP.S361106",
    "Beck, K., Beedle, M., van Bennekum, A., Cockburn, A., Cunningham, W., Fowler, M., Grenning, J., Highsmith, J., Hunt, A., Jeffries, R., Kern, J., Marick, B., Martin, R. C., Mellor, S., Schwaber, K., Sutherland, J., & Thomas, D. (2001). *Manifesto for agile software development*. https://agilemanifesto.org/",
    "Bochner, A. F., Makumbi, I., Aderinola, O., Abayneh, A., Jetoh, R., Yemanaberhan, R. L., Danjuma, J. S., Lazaro, F. T., Mahmoud, H. J., Yeabah, T. O., Nakiire, L., Yahaya, A. K., Teixeira, R. A., Lamorde, M., Nabukenya, I., Oladejo, J., Adetifa, I. M. O., Oliveira, W., McClelland, A., & Lee, C. T. (2023). Implementation of the 7-1-7 target for detection, notification, and response to public health threats in five countries: A retrospective, observational study. *The Lancet Global Health, 11*(6), e871–e879. https://doi.org/10.1016/S2214-109X(23)00133-X",
    "Boehme, K., Sia, S., Ablola, F., Gayeta, J., & Alea, M. C. (2022). Operational challenges of the Philippine Antimicrobial Resistance Surveillance Program during the COVID-19 pandemic. *Western Pacific Surveillance and Response Journal, 13*(3), 58–63. https://doi.org/10.5365/wpsar.2022.13.3.917",
    "Braun, V., & Clarke, V. (2006). Using thematic analysis in psychology. *Qualitative Research in Psychology, 3*(2), 77–101. https://doi.org/10.1191/1478088706qp063oa",
    "Cabaro, B., III, Dela Paz, G. A., Dotingco, J., Almirol, B. J., Borlongan, G., Cebreros, R. O., Diangco, P., Quijalvo, K. P., Tan, J. P., & Tonato, R. R. (2023). Establishing a national indicator-based surveillance system for hospital bed utilization by COVID-19 patients in the Philippines. *Western Pacific Surveillance and Response Journal, 14*(5), 33–39. https://doi.org/10.5365/wpsar.2023.14.5.1038",
    "Cardenas, R., Hussain-Alkhateeb, L., Benitez-Valladares, D., Sánchez-Tejeda, G., & Kroeger, A. (2022). The Early Warning and Response System (EWARS-TDR) for dengue outbreaks: Can it also be applied to chikungunya and Zika outbreak warning? *BMC Infectious Diseases, 22*, Article 235. https://doi.org/10.1186/s12879-022-07197-6",
    "Carvajal, T. M., Viacrusis, K. M., Hernandez, L. F. T., Ho, H. T., Amalin, D. M., & Watanabe, K. (2018). Machine learning methods reveal the temporal pattern of dengue incidence using meteorological factors in Metropolitan Manila, Philippines. *BMC Infectious Diseases, 18*, Article 183. https://doi.org/10.1186/s12879-018-3066-0",
    "Chen, X., & Moraga, P. (2025). Assessing dengue forecasting methods: A comparative study of statistical models and machine learning techniques in Rio de Janeiro, Brazil. *Tropical Medicine and Health, 53*, Article 52. https://doi.org/10.1186/s41182-025-00723-7",
    "Commission on Higher Education. (2010). *Revised policies, standards and guidelines for graduate program information technology education (ITE)* (CHED Memorandum Order No. 07, Series of 2010). https://legacy.ched.gov.ph/wp-content/uploads/2017/10/CMO-No.07-s2010.pdf",
    "Commission on Higher Education. (2019). *Policies, standards, and guidelines for graduate programs* (CHED Memorandum Order No. 15, Series of 2019). https://legacy.ched.gov.ph/2019-ched-memorandum-orders/",
    "de Claro, V., Lava, J. B., Bondoc, C., & Stan, L. (2024). The role of local health officers in advancing public health and primary care integration: Lessons from the ongoing Universal Health Coverage reforms in the Philippines. *BMJ Global Health, 9*(1), Article e014118. https://doi.org/10.1136/bmjgh-2023-014118",
    "De Mesa, R. Y. H., Galingana, C. L. T., Tan-Lim, C. S. C., Javelosa, M. A. U., Panganiban, J. M. S., Fabian, N. M. C., Calderon, Y., Rey, M. P., Bernal-Sundiang, N., Sanchez, J. T., Dans, L. F., Casile, R. U., & Dans, A. L. (2024). Facing the digital frontier: Exploring user acceptance of electronic health records in an urban, rural and remote setting in the Philippines. *BMJ Open Quality, 13*(2), Article e002621. https://doi.org/10.1136/bmjoq-2023-002621",
    "Department of Health. (2014). *Manual of procedures for the Philippine Integrated Disease Surveillance and Response* (3rd ed., Vol. 1). National Epidemiology Center.",
    "Dong, E., Du, H., & Gardner, L. (2020). An interactive web-based dashboard to track COVID-19 in real time. *The Lancet Infectious Diseases, 20*(5), 533–534. https://doi.org/10.1016/S1473-3099(20)30120-1",
    "Ester, M., Kriegel, H.-P., Sander, J., & Xu, X. (1996). A density-based algorithm for discovering clusters in large spatial databases with noise. In E. Simoudis, J. Han, & U. Fayyad (Eds.), *Proceedings of the Second International Conference on Knowledge Discovery and Data Mining* (pp. 226–231). AAAI Press.",
    "Fisher, R. P., & Myers, B. A. (2011). Free and simple GIS as appropriate for health mapping in a low resource setting: A case study in eastern Indonesia. *International Journal of Health Geographics, 10*, Article 15. https://doi.org/10.1186/1476-072X-10-15",
    "Franklin, N., Hope, K., Glass, K., & Kirk, M. (2025). Text message surveillance for rapid salmonella outbreak detection: A novel public health approach. *Epidemiology and Infection, 153*, Article e118. https://doi.org/10.1017/S0950268825100617",
    "Freifeld, C. C., Mandl, K. D., Reis, B. Y., & Brownstein, J. S. (2008). HealthMap: Global infectious disease monitoring through automated classification and visualization of Internet media reports. *Journal of the American Medical Informatics Association, 15*(2), 150–157. https://doi.org/10.1197/jamia.M2544",
    "Fuad, M. M., Milki, M. S., & Aziz, R. A. (2026). Tactical vs. strategic: An adaptable framework for horizon-dependent dengue forecasting using data-driven approaches with serotype and climate covariates in Bangladesh. *PLOS One, 21*(8), Article e0353069. https://doi.org/10.1371/journal.pone.0353069",
    "Fuller, B., Ssekitoleko, R., Kyozira, C., Colston, J. M., Makumbi, I., Bakainaga, A., Moore, C. C., & Kiirya, H. I. (2025). Comparison of ARIMA and FB-Prophet time series models for the prediction of national and regional malaria incidence in Uganda. *Malaria Journal, 24*, Article 289. https://doi.org/10.1186/s12936-025-05547-8",
    "García, G. A., Atkinson, B., Donfack, O. T., Hilton, E. R., Smith, J. M., Eyono, J. N. M., Iyanga, M. M., Vaz, L. M., Mba Nguema Avue, R., Pollock, J., Ratsirarson, J., Aldrich, E. M., Phiri, W. P., Smith, D. L., Schwabe, C., & Guerra, C. A. (2022). Real-time, spatial decision support to optimize malaria vector control: The case of indoor residual spraying on Bioko Island, Equatorial Guinea. *PLOS Digital Health, 1*(5), Article e0000025. https://doi.org/10.1371/journal.pdig.0000025",
    "German, R. R., Lee, L. M., Horan, J. M., Milstein, R. L., Pertowski, C. A., & Waller, M. N. (2001). Updated guidelines for evaluating public health surveillance systems: Recommendations from the Guidelines Working Group. *MMWR Recommendations and Reports, 50*(RR-13), 1–35. https://www.cdc.gov/mmwr/preview/mmwrhtml/rr5013a1.htm",
    "Gouveia, A. S., Gomes, M. F. da C., de Almeida, I. F., Lana, R. M., Bastos, L. S., Bianchi, L. M., Oliveira, S. de S., Araujo, E. C., Ferreira, D. A. da C., Oliveira, D. M. B., Godinho, V. B., Vacaro, L. B., Riback, T. I. S., Cruz, O. G., Coelho, F. C., & Codeço, C. T. (2025). Unraveling regional variability in dengue outbreaks in Brazil: Leveraging the Moving Epidemics Method (MEM) and climate data to optimize vector control strategies. *PLOS Neglected Tropical Diseases, 19*(6), Article e0013175. https://doi.org/10.1371/journal.pntd.0013175",
    "He, Y., Aliyu, A., Evans, M., & Luo, C. (2021). Health care cybersecurity challenges and solutions under the climate of COVID-19: Scoping review. *Journal of Medical Internet Research, 23*(4), Article e21747. https://doi.org/10.2196/21747",
    "Herbuela, V. R. D. M., Karita, T., Carvajal, T. M., Ho, H. T., Lorena, J. M. O., Regalado, R. A., Sobrepeña, G. D., & Watanabe, K. (2021). Early detection of dengue fever outbreaks using a surveillance app (Mozzify): Cross-sectional mixed methods usability study. *JMIR Public Health and Surveillance, 7*(3), Article e19034. https://doi.org/10.2196/19034",
    "Hu, W.-H., Sun, H.-M., Wei, Y.-Y., & Hao, Y.-T. (2025). Global infectious disease early warning models: An updated review and lessons from the COVID-19 pandemic. *Infectious Disease Modelling, 10*(2), 410–422. https://doi.org/10.1016/j.idm.2024.12.001",
    "Hutwagner, L., Thompson, W., Seeman, G. M., & Treadwell, T. (2003). The bioterrorism preparedness and response Early Aberration Reporting System (EARS). *Journal of Urban Health, 80*(2 Suppl. 1), i89–i96. https://doi.org/10.1007/PL00022319",
    "Ibrahim, L. M., Okudo, I., Stephen, M., Ogundiran, O., Pantuvo, J. S., Oyaole, D. R., Tegegne, S. G., Khalid, A., Ilori, E., Ojo, O., Ihekweazu, C., Baraka, F., Mulombo, W. K., Lasuba, C. L. P., Nsubuga, P., & Alemu, W. (2021). Electronic reporting of integrated disease surveillance and response: Lessons learned from northeast, Nigeria, 2019. *BMC Public Health, 21*, Article 916. https://doi.org/10.1186/s12889-021-10957-9",
    "International Organization for Standardization & International Electrotechnical Commission. (2023). *Systems and software engineering: Systems and software Quality Requirements and Evaluation (SQuaRE): Product quality model* (ISO/IEC Standard No. 25010:2023). https://www.iso.org/standard/78176.html",
    "Joseph, J. J., Mkali, H. R., Reaves, E. J., Mwaipape, O. S., Mohamed, A., Lazaro, S. N., Aaron, S., Chacky, F., Mahendeka, A., Rulagirwa, H. S., Mwenesi, M., Mwakapeje, E., Ally, A. Y., Kitojo, C., Serbantez, N., Nyinondi, S., Lalji, S. M., Wilillo, R., Al-mafazy, A.-W., . . . Ngondi, J. M. (2022). Improvements in malaria surveillance through the electronic Integrated Disease Surveillance and Response (eIDSR) system in mainland Tanzania, 2013–2021. *Malaria Journal, 21*, Article 321. https://doi.org/10.1186/s12936-022-04353-w",
    "Kaburi, B. B., Wyss, K., Kenu, E., Asiedu-Bekoe, F., Hauri, A. M., Laryea, D. O., Klett-Tammen, C. J., Leone, F., Walter, C., & Krause, G. (2023). Facilitators and barriers in the implementation of a digital surveillance and outbreak response system in Ghana before and during the COVID-19 pandemic: Qualitative analysis of stakeholder interviews. *JMIR Formative Research, 7*, Article e45715. https://doi.org/10.2196/45715",
    "Kannampallil, T., & Adler-Milstein, J. (2022). Using electronic health record audit log data for research: Insights from early efforts. *Journal of the American Medical Informatics Association, 30*(1), 167–171. https://doi.org/10.1093/jamia/ocac173",
    "Klaucke, D. N., Buehler, J. W., Thacker, S. B., Parrish, R. G., Trowbridge, F. L., & Berkelman, R. L. (1988). Guidelines for evaluating surveillance systems. *Morbidity and Mortality Weekly Report, 37*(Suppl. 5), 1–18. https://www.cdc.gov/mmwr/preview/mmwrhtml/00001769.htm",
    "Lawson, A. B. (2018). *Bayesian disease mapping: Hierarchical modeling in spatial epidemiology* (3rd ed.). Chapman and Hall/CRC. https://doi.org/10.1201/9781351271769",
    "Lee, B., Dupervil, B., Deputy, N. P., Duck, W., Soroka, S., Bottichio, L., Silk, B., Price, J., Sweeney, P., Fuld, J., Weber, J. T., & Pollock, D. (2021). Protecting privacy and transforming COVID-19 case surveillance datasets for public use. *Public Health Reports, 136*(5), 554–561. https://doi.org/10.1177/00333549211026817",
    "Low, G. K. K., Jiee, S. F., Lim, S. H., Omosumwen, O. F., & Shanmuganathan, S. (2025). The effectiveness of dengue vector control: A meta-review. *Tropical Medicine & International Health, 30*(10), 1069–1086. https://doi.org/10.1111/tmi.70018",
    "Mamani-Pari, D., Peñaloza-Hualpa, A. F., Humpiri-Flores, M. E., Gutierrez-Quispe, E., & Otazu-Luque, J. E. (2026). Development and psychometric validation of a usability instrument based on ISO 25010 for electronic health record systems in Peruvian health care settings: Methodological study. *JMIR Human Factors, 13*, Article e81377. https://doi.org/10.2196/81377",
    "Manahan, K. M., De Guzman, A., Segarra, A., Sucaldito, M. N., & Martinez, R. E. (2024). Establishing an early warning surveillance system in jails in Calabarzon, the Philippines, 2021. *Western Pacific Surveillance and Response Journal, 15*(2), 19–25. https://doi.org/10.5365/wpsar.2024.15.2.1083",
    "Maravilla, J., Catiwa, J., Guariño, R., Yap, J. F., Pagatpatan, C., Orolfo, D. D., de Silos, J., Leigh, M. C., Babate, J., & Lopez, V. (2023). Exploring indirect impacts of COVID-19 on local health systems from the perspectives of health workers and higher education stakeholders in the Philippines using a phenomenological approach. *The Lancet Regional Health – Western Pacific, 30*, Article 100585. https://doi.org/10.1016/j.lanwpc.2022.100585",
    "Medina, J. R. C., Kawamura, S., Takeuchi, R., Cruz, R. V., Mendoza, J., Hernandez, P. M. R., Garcia, F. B., Gregorio, E. R., & Kobayashi, J. (2025). Pre- and post-COVID-19 pandemic identification of dengue hotspots and exploration of population and environmental determinants of dengue in Quezon City, Philippines. *Tropical Medicine and Health, 53*, Article 109. https://doi.org/10.1186/s41182-025-00789-3",
    "Medina, J. R. C., Takeuchi, R., Mercado, C. E. G., de los Reyes, C. S., Cruz, R. V., Abrigo, M. D. R., Hernandez, P. M. R., Garcia, F. B., Salanguit, M., Gregorio, E. R., Kawamura, S., Hung, K. E., Kaneko, M., Nonaka, D., Maude, R. J., & Kobayashi, J. (2023). Spatial and temporal distribution of reported dengue cases and hot spot identification in Quezon City, Philippines, 2010–2017. *Tropical Medicine and Health, 51*, Article 31. https://doi.org/10.1186/s41182-023-00523-x",
    "Murai, S., Ventura, R. J. C., & Gaite, J. T. (2022). Timeliness of reporting process in the national routine health information system: The case of 19-year experience of Field Health Services Information System in Palawan, the Philippines. *PLOS ONE, 17*(2), Article e0264681. https://doi.org/10.1371/journal.pone.0264681",
    "Nageshwaran, G., Harris, R. C., & Guerche-Seblain, C. E. (2021). Review of the role of big data and digital technologies in controlling COVID-19 in Asia: Public health interest vs. privacy. *Digital Health, 7*, Article 20552076211002953. https://doi.org/10.1177/20552076211002953",
    "Nansikombi, H. T., Kwesiga, B., Aceng, F. L., Ario, A. R., Bulage, L., & Arinaitwe, E. S. (2023). Timeliness and completeness of weekly surveillance data reporting on epidemic prone diseases in Uganda, 2020–2021. *BMC Public Health, 23*, Article 647. https://doi.org/10.1186/s12889-023-15534-w",
    "National Privacy Commission. (2016, December 15). *NPC Circular No. 16-03: Personal data breach management*. https://privacy.gov.ph/npc-circular-16-03-personal-data-breach-management/",
    "National Privacy Commission. (2023). *NPC Circular No. 2023-06: Security of personal data in the government and the private sector*. https://privacy.gov.ph/",
    "Neprash, H. T., McGlave, C. C., Cross, D. A., Virnig, B. A., Puskarich, M. A., Huling, J. D., Rozenshtein, A. Z., & Nikpay, S. S. (2022). Trends in ransomware attacks on US hospitals, clinics, and other health care delivery organizations, 2016–2021. *JAMA Health Forum, 3*(12), Article e224873. https://doi.org/10.1001/jamahealthforum.2022.4873",
    "Nykiforuk, C. I. J., & Flaman, L. M. (2011). Geographic information systems (GIS) for health promotion and public health: A review. *Health Promotion Practice, 12*(1), 63–73. https://doi.org/10.1177/1524839909334624",
    "Olana, K. O. A., Poprom, N., Siewchaisakul, P., Punyapornwithaya, V., & Thongprachum, A. (2025). Spatial distribution analysis and comparative forecasting of dengue resurgence in the Philippines (2025–2027): A nationwide study. *Transboundary and Emerging Diseases, 2025*(1), Article 7480710. https://doi.org/10.1155/tbed/7480710",
    "Olana, K. O. A., Thongprachum, A., Poprom, N., Li, W., & Punyapornwithaya, V. (2025). Determination of dengue high-risk areas in the Philippines: A kernel density estimation, inverse distance weighting, and ecological niche modeling. *Parasites & Vectors, 19*, Article 48. https://doi.org/10.1186/s13071-025-07200-4",
    "Olana, K. O. A., Thongprachum, A., Poprom, N., & Punyapornwithaya, V. (2026). Spatiotemporal clusters and dengue hotspots in the Philippines: A nationwide analysis spanning 2017–2024. *Frontiers in Public Health, 14*, Article 1781800. https://doi.org/10.3389/fpubh.2026.1781800",
    "Ong, K. P. (2026). Implementation of fireworks-related injury surveillance in Metro Manila, Philippines, 2023–2024. *Western Pacific Surveillance and Response Journal, 17*(1), 53–60. https://doi.org/10.5365/wpsar.2026.17.1.1272",
    "Osako, H., Tayama, Y., Ueda, M., Ihara, M., Yamasato, K., Tun, M. M. N., Thuy, N. T. T., Hang, N. L. K., Phuong, H. V. M., Abe, H., Hashizume, M., Hasebe, F., Takamatsu, Y., & Mai, L. T. Q. (2026). Comprehensive spatiotemporal analysis of dengue epidemics in Vietnam reveals key hotspots and transmission dynamics. *International Journal of Infectious Diseases, 165*, Article 108445. https://doi.org/10.1016/j.ijid.2026.108445",
    "Pepito, V. C. F., Loreche, A. M., Legaspi, R. S., Guinaran, R. C., Capeding, T. P. J. Z., Ong, M. M., & Dayrit, M. M. (2025). Health workforce issues and recommended practices in the implementation of Universal Health Coverage in the Philippines: A qualitative study. *Human Resources for Health, 23*, Article 21. https://doi.org/10.1186/s12960-025-00988-3",
    "Philippine Health Research Ethics Board. (2022). *National ethical guidelines for research involving human participants 2022*. Philippine Council for Health Research and Development. https://www.pchrd.dost.gov.ph/wp-content/uploads/2023/05/2022-NEGRIHP_Official-Gazatte_Ver-5-1.pdf",
    "Prakash Nayak, P., Pai B., J., & Govindan, S. (2025). Leveraging geographic information system for dengue surveillance: A scoping review. *Tropical Medicine and Health, 53*, Article 102. https://doi.org/10.1186/s41182-025-00783-9",
    "Rajvanshi, H., Jain, Y., Kaintura, N., Soni, C., Chandramohan, R., Srinivasan, R., Telasey, V., Bharti, P. K., Jain, D., Surve, M., Saxena, S., Gangamwar, V., Anand, M. S., & Lal, A. A. (2021). A comprehensive mobile application tool for disease surveillance, workforce management and supply chain management for Malaria Elimination Demonstration Project. *Malaria Journal, 20*, Article 91. https://doi.org/10.1186/s12936-021-03623-3",
    "Rattananen, M., Sahavechaphan, N., & Areechokchai, D. (2025). Identifying high-risk subdistricts for targeted dengue interventions: A spatio-temporal study in Mueang Chonburi district, Thailand, 2011–2020. *BMC Public Health, 26*, Article 303. https://doi.org/10.1186/s12889-025-25952-7",
    "Ravishankar, N., Mathauer, I., Barroy, H., Vîlcu, I., Chaitkin, M., Offosse, M. J., Co, P. A., Nakyanzi, A., Mbuthia, B., Lourenço, S., Mardani, H., & Kutzin, J. (2024). Reconciling devolution with health financing and public financial management: Challenges and policy options for the health sector. *BMJ Global Health, 9*(5), Article e015216. https://doi.org/10.1136/bmjgh-2024-015216",
    "Republic Act No. 10173. (2012). *An act protecting individual personal information in information and communications systems in the government and the private sector, creating for this purpose a National Privacy Commission, and for other purposes* (Data Privacy Act of 2012). https://www.officialgazette.gov.ph/2012/08/15/republic-act-no-10173/",
    "Reynolds, E., Martel, L. D., Bah, M. O., Bah, M., Bah, M. B., Boubacar, B., Camara, N., Camara, Y. B., Corvil, S., Diallo, B. I., Diallo, I. T., Diallo, M. K., Diallo, M. T., Diallo, T., Guilavogui, S., Hemingway-Foday, J. J., Hann, F., Kaba, A., Kaba, A. K., . . . MacDonald, P. D. M. (2022). Implementation of DHIS2 for disease surveillance in Guinea: 2015–2020. *Frontiers in Public Health, 9*, Article 761196. https://doi.org/10.3389/fpubh.2021.761196",
    "Richey, R. C., & Klein, J. D. (2007). *Design and development research: Methods, strategies, and issues*. Lawrence Erlbaum Associates.",
    "Rotejanaprasert, C., Chinpong, K., Lawson, A. B., & Maude, R. J. (2024). Comparative evaluation of spatiotemporal methods for effective dengue cluster detection with a case study of national surveillance data in Thailand. *Scientific Reports, 14*, Article 31064. https://doi.org/10.1038/s41598-024-82212-1",
    "Saadatian-Elahi, M., Rabilloud, M., Möhlmann, T. W. R., Langlois-Jacques, C., Ariffin, F. D., Farenhorst, M., Elsensohn, M.-H., Schmitt, F., Richardson, J. H., Baur, F., Leduc, M., Romli, N. N., Tan, L. K., Norazman, M.-R., Shahar, H., Mudin, R. N., Alexander, N., & Ab Hamid, N. (2025). Effectiveness of integrated vector management on the incidence of dengue in urban Malaysia: A cluster-randomised controlled trial. *The Lancet Infectious Diseases, 25*(9), 977–985. https://doi.org/10.1016/S1473-3099(25)00086-6",
    "Sanchez Tejeda, G., Benitez Valladares, D., Correa Morales, F., Toledo Cisneros, J., Espinoza Tamarindo, B. E., Hussain-Alkhateeb, L., Merle, C. S., & Kroeger, A. (2023). Early warning and response system for dengue outbreaks: Moving from research to operational implementation in Mexico. *PLOS Global Public Health, 3*(9), Article e0001691. https://doi.org/10.1371/journal.pgph.0001691",
    "Santos-Silva, R., Florentino, P. T. V., Cerqueira-Silva, T., Oliveira, V. de A., Bertoldo Junior, J., Barbosa, G. C., Penna, G. O., Boaventura, V. S., Ramos, P. I. P., Barral-Netto, M., & Marcilio, I. (2025). Primary health care data-based early warning system for dengue outbreaks: A nationwide case study in Brazil. *The Lancet Regional Health – Americas, 48*, Article 101165. https://doi.org/10.1016/j.lana.2025.101165",
    "Schneider, R., Domakonda, K., Bhandari, S., Stadler, L., Ensor, K. B., Mulenga, A., Johnson, C. D., & Hopkins, L. (2025). Implementing an alert system for communicating actionable wastewater surveillance results to school communities, Houston, Texas, 2023–2024. *Public Health Reports, 140*(2–3), 150–155. https://doi.org/10.1177/00333549241275408",
    "Sena, B. F., Herrera, B. B., Martins, D. B. G., & Lima Filho, J. L. (2025). Geospatial clustering reveals dengue hotspots across Brazilian municipalities, 2024. *Frontiers in Public Health, 13*, Article 1620914. https://doi.org/10.3389/fpubh.2025.1620914",
    "Shea, K., Borchering, R. K., Probert, W. J. M., Howerton, E., Bogich, T. L., Li, S.-L., van Panhuis, W. G., Viboud, C., Aguás, R., Belov, A. A., Bhargava, S. H., Cavany, S. M., Chang, J. C., Chen, C., Chen, J., Chen, S., Chen, Y., Childs, L. M., Chow, C. C., . . . Runge, M. C. (2023). Multiple models for outbreak decision support in the face of uncertainty. *Proceedings of the National Academy of Sciences, 120*(18), Article e2207537120. https://doi.org/10.1073/pnas.2207537120",
    "Stroup, D. F., Williamson, G. D., Herndon, J. L., & Karon, J. M. (1989). Detection of aberrations in the occurrence of notifiable diseases surveillance data. *Statistics in Medicine, 8*(3), 323–329. https://doi.org/10.1002/sim.4780080312",
    "Sucaldito, M. S. F., Malhotra, R., Palileo-Villanueva, L., Besa, J. J., Echague, P. A., Saquilayan, M. J., Banzuela, J. M., Mendoza, K., Elepaño, A., Yan, L. L., & Østbye, T. (2025). Challenges and opportunities for health information systems in primary care clinics: A mixed-method study among health workers in Manila, Philippines. *Applied Clinical Informatics, 16*(4), 1077–1085. https://doi.org/10.1055/a-2595-2824",
    "Taylor, S. J., & Letham, B. (2018). Forecasting at scale. *The American Statistician, 72*(1), 37–45. https://doi.org/10.1080/00031305.2017.1380080",
    "Thayer, M. B., Marzan-Rodriguez, M., Torres Aponte, J., Rivera, A., Rodriguez, D. M., Madewell, Z. J., Rysava, K., Paz-Bailey, G., Adams, L. E., & Johansson, M. A. (2025). Dengue epidemic alert thresholds for surveillance and decision-making in Puerto Rico: Development and prospective application of an early warning system using routine surveillance data. *BMJ Open, 15*(9), Article e106182. https://doi.org/10.1136/bmjopen-2025-106182",
    "Villanueva-Miranda, I., Xiao, G., & Xie, Y. (2025). Artificial intelligence in early warning systems for infectious disease surveillance: A systematic review. *Frontiers in Public Health, 13*, Article 1609615. https://doi.org/10.3389/fpubh.2025.1609615",
    "World Health Organization. (2009). *Dengue: Guidelines for diagnosis, treatment, prevention and control* (New ed., WHO/HTM/NTD/DEN/2009.1). https://www.who.int/publications/i/item/9789241547871",
    "World Health Organization. (2014). *Early detection, assessment and response to acute public health events: Implementation of early warning and response with a focus on event-based surveillance* (Interim version; WHO/HSE/GCR/LYO/2014.4). https://iris.who.int/handle/10665/112667",
    "Ygoña, J., Deligero, E., & Ceballos, R. (2025). Spatio-temporal analysis of dengue in the Philippines: The case of South Cotabato. *Recoletos Multidisciplinary Research Journal, 13*(1), 33–43. https://doi.org/10.32871/rmrj2513.01.03",
    "Zuniga, P. C., Carpio, J. J., Tayam, Q. A., Garcia, P. L., Lacsina, A., Calderon, J., Santiago, J. F., & Batangan, D. (2026). Development and implementation of an interoperable local health information exchange platform for the attainment of universal health coverage in the Philippines. *Frontiers in Digital Health, 7*, Article 1650273. https://doi.org/10.3389/fdgth.2025.1650273",
]

for ref in refs:
    p = doc.add_paragraph()
    # TUP format reference: hanging indent (0.5"), single-spaced entries with
    # one blank line (12 pt) between them.
    p.paragraph_format.left_indent = Inches(0.5)
    p.paragraph_format.first_line_indent = Inches(-0.5)
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(12)
    p.paragraph_format.line_spacing = 1.0
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    # Parse *italic* markers and emit italic runs for journal/book/report titles
    # per APA 7 §9.18-9.25. Segments between * pairs render italic; the rest
    # renders plain. Asterisks themselves are stripped at render time.
    parts = ref.split("*")
    for i, part in enumerate(parts):
        if not part:
            continue
        r = p.add_run(part)
        r.font.name = "Times New Roman"
        r.font.size = Pt(12)
        if i % 2 == 1:  # odd-indexed segments are between asterisks
            r.italic = True

doc.save(OUT_PATH)
print(f"WROTE {OUT_PATH}")
