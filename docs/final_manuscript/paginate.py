"""Fills the Table of Contents and lists with real page numbers.

Builds the manuscript, renders it to PDF through Microsoft Word, finds the page
of every TOC heading, table, and figure, writes page_map.json, and rebuilds
until the numbers stop changing.

Usage: python paginate.py
"""
import json
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
DOCX = HERE / "Chapters_1to3_Final_Revision.docx"
PDF = HERE / "Chapters_1to3_Final_Revision.pdf"
MAP = HERE / "page_map.json"

sys.path.insert(0, str(HERE))


def roman(n):
    vals = [(10, "x"), (9, "ix"), (5, "v"), (4, "iv"), (1, "i")]
    out = ""
    for v, s in vals:
        while n >= v:
            out += s
            n -= v
    return out


def build_and_render():
    subprocess.run([sys.executable, str(HERE / "build_chapters_final.py")], check=True)
    subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
                    str(HERE / "docx_to_pdf.ps1"), str(DOCX), str(PDF)], check=True)
    text = subprocess.run(["pdftotext", "-layout", str(PDF), "-"], capture_output=True,
                          text=True, encoding="utf-8", errors="replace").stdout
    return [[ln.strip() for ln in page.splitlines()] for page in text.split("\f")]


def page_map(pages):
    # the build module defines the TOC entries; import without executing the build
    src = (HERE / "build_chapters_final.py").read_text(encoding="utf-8")
    entries = eval(re.search(r"TOC_ENTRIES = (\[.*?\n\])", src, re.S).group(1))
    n_tables = len(eval(re.search(r"LIST_OF_TABLES = (\[.*?\n\])", src, re.S).group(1)))
    n_figures = len(eval(re.search(r"LIST_OF_FIGURES = (\[.*?\n\])", src, re.S).group(1)))

    body_start = next(i for i, p in enumerate(pages) if "Chapter 1" in p)
    found = {"Title Page": "i"}
    for name in ("TABLE OF CONTENTS", "LIST OF TABLES", "LIST OF FIGURES"):
        idx = next(i for i, p in enumerate(pages[:body_start]) if name in p)
        found[name.title().replace("Of", "of")] = roman(idx + 1)

    def body_page(match, start=body_start):
        for i in range(start, len(pages)):
            if any(match(ln) for ln in pages[i]):
                return i
        raise LookupError

    cursor = body_start
    for text, kind in entries:
        if kind != "section":
            continue
        target = "References" if text == "REFERENCES" else text
        i = body_page(lambda ln, t=target: ln == t, cursor)
        found[text] = str(i - body_start + 1)
        cursor = i
    for n in range(1, n_tables + 1):
        i = body_page(lambda ln, n=n: ln == f"Table {n}")
        found[f"Table {n}"] = str(i - body_start + 1)
    for n in range(1, n_figures + 1):
        i = body_page(lambda ln, n=n: ln.startswith(f"Figure {n}."))
        found[f"Figure {n}"] = str(i - body_start + 1)
    return found


previous = None
for attempt in range(1, 4):
    current = page_map(build_and_render())
    MAP.write_text(json.dumps(current, indent=1), encoding="utf-8")
    print(f"pass {attempt}: {len(current)} entries")
    if current == previous:
        break
    previous = current
else:
    subprocess.run([sys.executable, str(HERE / "build_chapters_final.py")], check=True)
print(json.dumps(current, indent=1))
