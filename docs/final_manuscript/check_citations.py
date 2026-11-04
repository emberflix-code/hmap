"""Cross-checks in-text citations against the reference list of the built manuscript.

Usage: python check_citations.py <manuscript.docx>
"""
import re
import sys
import unicodedata

import docx


def fold(s):
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()


d = docx.Document(sys.argv[1])
paras = [p.text for p in d.paragraphs]
cells = [c.text for t in d.tables for r in t.rows for c in r.cells]
ref_start = max(i for i, t in enumerate(paras) if t.strip() == "References")
body = "\n".join(paras[:ref_start] + cells)
refs = [t for t in paras[ref_start + 1:] if t.strip()]

# reference keys: first author surname (or corporate author) + year
ref_keys = {}
for r in refs:
    m = re.match(r"^(.+?)\.?\s\((\d{4})", r)
    if not m:
        print("UNPARSED REF:", r[:80])
        continue
    first = m.group(1).split(",")[0].strip()
    ref_keys[(fold(first), m.group(2))] = r[:70]

# in-text citations: "Surname et al., 2023", "Surname & Other, 2023", "Surname (2023)", corporate
pat = re.compile(r"([A-Z][A-Za-zÀ-ÿ'\-]+(?: [A-Z][A-Za-zÀ-ÿ'\-]+)*)(?:,? (?:et al\.|& [A-Z][^,()]+?|"
                 r"[A-Z][A-Za-z\-]+, et al\.))?,? \(?((?:19|20)\d{2})")
cited = set()
for m in pat.finditer(body):
    name = m.group(1).split()[-1] if m.group(1).split()[0] in ("In", "The", "See") else m.group(1)
    cited.add((fold(name.strip()), m.group(2)))

aliases = {("doh", "2014"): ("department of health", "2014"),
           ("ched", "2010"): ("commission on higher education", "2010"),
           ("ched", "2019"): ("commission on higher education", "2019"),
           ("npc", "2016"): ("national privacy commission", "2016"),
           ("npc", "2023"): ("national privacy commission", "2023"),
           ("who", "2009"): ("world health organization", "2009"),
           ("who", "2014"): ("world health organization", "2014"),
           ("phreb", "2022"): ("philippine health research ethics board", "2022")}
for k, v in aliases.items():
    if re.search(rf"\b{k[0].upper()}\b[^()]*?{k[1]}", body):
        cited.add(v)
if "ISO/IEC, 2023" in body or "[ISO/IEC], 2023" in body:
    cited.add(("international organization for standardization & international electrotechnical commission", "2023"))
if "Republic Act No. 10173 (2012" in body or "Republic Act No. 10173, 2012" in body:
    cited.add(("republic act no", "2012"))

ref_first = {(k[0].split(" & ")[0], k[1]): v for k, v in ref_keys.items()}
missing = sorted(c for c in cited if (c[0], c[1]) not in ref_first
                 and not any(c[0] in rk[0] and c[1] == rk[1] for rk in ref_first))
uncited = sorted(k for k in ref_first if not any(c[1] == k[1] and (c[0] in k[0] or k[0] in c[0])
                                                  for c in cited))
print("references:", len(refs))
print("\nCITED BUT NOT IN REFERENCES (check, may include false positives):")
for c in missing:
    print("  ", c)
print("\nIN REFERENCES BUT NOT CITED:")
for k in uncited:
    print("  ", k, ref_first[k])
print("\nleftovers: H-MAP =", body.count("H-MAP"), "| [CITE =", body.count("[CITE"),
      "| em dashes =", body.count("—"), "| placeholders =", body.count("[placeholder"))
