"""Mechanical style checks on the built manuscript body (not the references).

Usage: python check_style.py <manuscript.docx>
"""
import re
import sys
from collections import Counter

import docx

d = docx.Document(sys.argv[1])
paras = [p.text for p in d.paragraphs]
start = next(i for i, t in enumerate(paras) if t.strip() == "Chapter 1")
end = max(i for i, t in enumerate(paras) if t.strip() == "References")
body = [t for t in paras[start:end] if t.strip()]
text = "\n".join(body)

print("== doubled words")
for m in re.finditer(r"\b(\w+) \1\b", text, re.I):
    print("  ", text[max(0, m.start() - 40):m.end() + 20].replace("\n", " "))

print("== double spaces / space before punctuation")
for m in re.finditer(r"\S  +\S| [,.;:)]", text):
    print("  ", repr(text[max(0, m.start() - 30):m.end() + 10]))

print("== sentences over 60 words")
for s in re.split(r"(?<=[.!?])\s+(?=[A-Z])", text):
    n = len(s.split())
    if n > 60:
        print(f"   ({n} words) {s[:110]}...")

print("== variant spellings (each group should use one form)")
groups = [["spatio-temporal", "spatiotemporal", "spatio temporal"],
          ["e-mail", "email"], ["data set", "dataset"], ["web-based", "web based"],
          ["decision-support", "decision support"], ["health care", "healthcare"],
          ["%", " percent"], ["Covid-19", "COVID-19"], ["geocod", "geo-cod"],
          ["vector-control", "vector control"], ["real-time", "real time"]]
low = text.lower()
for g in groups:
    counts = {v: low.count(v.lower()) for v in g}
    used = {k: c for k, c in counts.items() if c}
    if len(used) > 1:
        print("  ", used)

print("== future tense in Ch.1-3 (should be present)")
for m in re.finditer(r"\bwill (be |)\w+", text):
    print("  ", text[max(0, m.start() - 50):m.end() + 20].replace("\n", " "))

print("== first-person or informal words")
for w in ["we ", "our ", " I ", "very ", "really", "a lot", "etc."]:
    c = text.count(w)
    if c:
        print(f"   {w!r}: {c}")
