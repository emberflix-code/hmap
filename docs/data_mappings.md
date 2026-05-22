# PIDSR Registry → H-MAP Canonical Mappings

**Current source:** `docs/PIDSR Report YR 2026.xlsx`, sheet `Registry` (35,706 rows, 2010–2026 YTD).
ETL auto-picks the newest `PIDSR Report YR NNNN.xlsx` from `docs/` by year-in-filename, so dropping in a future export switches the source without code changes.

**Purpose.** Document every normalization rule applied to the raw CESU line list when loading into `hmap_db.cases`. The thesis can defend every value-level decision against this file.

## At a glance

| | Raw (in `Registry`) | Canonical (in `hmap_db`) |
|---|---|---|
| Disease strings | 63 distinct | 21 PIDSR diseases (Dengue, ILI, Measles, Lepto, Typhoid, HFMD, ABD, COVID-19, AVH, BMENG, NNT, NT, ROTA, AES, AFP, DIP, AHFS, RAB, MAL, PER, AEFI, RUB, CHK, SARS, ZIKA, CHO — observed; 8 more PIDSR-listed but unobserved, seeded for completeness) |
| Barangay strings | 24 distinct | 16 official Parañaque barangays |
| CASECLASS values | 82 distinct | 7 PIDSR canonical (Suspect / Probable / Confirmed / Compatible / Discarded / Negative / Pending) |
| Outcome values | 3 distinct (`A`/`a`/`D`) | 3 (Alive / Died / Unknown) |

### Reconciliation against the live database

```
Registry source rows:       35,706
→ cases (loaded):           35,164
→ excluded_cases (audit):      542
    out_of_city                25
    unknown_barangay          517
Reconciliation:             MATCH
```

Case-classification distribution in the loaded `cases` table:

```
Suspect      14,730
Probable     12,340
Confirmed     6,122
Pending       1,446
Discarded       302
Compatible      190
Negative         34
```

### Mojibake fix

Source file is mis-encoded for Ñ — every `Ñ` reads as `�` (`Para�aque`, `SANTO NI�O`). ETL restores Ñ at import; canonical names below use the correct character.

### File-version history

| Source file | Rows | Year range | Notes |
|---|---|---|---|
| `PIDSR Report YR 2023.xlsx` | 30,134 | 2010–2023 | Initial dataset. 2023 was a partial-year snapshot (491 rows). 247 rows had missing year/week (`invalid_data`). 14 non-Parañaque barangay strings (`BICUTAN`, `LAS PIÑAS`, `TAGUIG`, etc.). |
| `PIDSR Report YR 2026.xlsx` | 35,706 | 2010–2026 | **Current.** Complete 2023 (1,476), full 2024 (2,521), 2025 (1,928), 2026 YTD (158). CESU cleaned upstream: zero `invalid_data` rows; out-of-city barangay strings mostly removed; `Covid-19` and `Diphtheria` (correct spelling) variants appear; measles classifications expanded (`Lab Confirmed Measles`, `Epi-Linked`, etc.) requiring a tighter CASECLASS normalizer. |

---

## 1. Disease mapping

The raw `Disease` column conflates three concepts that PIDSR treats separately: the **disease itself**, the **case classification** (when the encoder put e.g. `Measles_Suspect` in the disease cell instead of in `CASECLASS`), and the **patient residency** (Parañaque resident vs. out-of-city referral). The ETL splits these into the proper columns.

Row counts in this section are from the 2026 file.

### Dengue (25,605 mapped rows)

| Raw `Disease` string | → canonical | classification | resident | Rows |
|---|---|---|---|---|
| `Dengue`, `DENGUE` | Dengue | (keep `CASECLASS`) | true | 25,596 |
| `Dengue_Not Pque`, `Dengue_not pque`, `Dengue_Not Resident`, `Dengue_Not Admitted`, `Dengue_Muntinlupa`, `Dengue_Pasay`, `Dengue_Not Pque_Las Piñas` | Dengue | (keep `CASECLASS`) | **false** → excluded | 17 |

Out-of-city referrals are audited to `excluded_cases` (reason `out_of_city`), per scope ("limited to the 16 barangays … does not include cases from adjacent cities").

### Measles (3,007 mapped rows + 5 out-of-city)

Measles has the most variants because lab-classification was historically encoded into the disease cell.

| Raw `Disease` string | → canonical | classification override | resident | Rows |
|---|---|---|---|---|
| `Measles` | Measles | — | true | 2,777 |
| `Measles_Suspect`, `Measles Suspect` | Measles | **Suspect** | true | 52 |
| `Measles_Discarded` | Measles | **Discarded** | true | 77 |
| `Measles Compatible` | Measles | **Compatible** | true | 37 |
| `Measles - Negative`, `Measles Negative` | Measles | **Negative** | true | 25 |
| `Measles - pending`, `Measles_Suspect_Pending` | Measles | **Pending** | true | 5 |
| `Measles_Not Pque`, `Measles_las pinas`, `Measles_Muntinlupa`, `Measles_no pque`, `Measles_not pque` | Measles | (keep `CASECLASS`) | **false** → excluded | 5 |

Override means: when the disease string encodes a classification (`Measles_Suspect`), ETL writes that classification into `case_classification` and ignores whatever was in the raw `CASECLASS` column.

### All other diseases

| Raw `Disease` string(s) | → canonical | classification | resident | Rows |
|---|---|---|---|---|
| `Influenza Like Illness`, `Influenza Like illness` (casing) | Influenza-Like Illness | — | true | 3,442 |
| `Leptospirosis` | Leptospirosis | — | true | 943 |
| `Typhoid Fever` | Typhoid Fever | — | true | 865 |
| `Hand, Foot & Mouth Disease` | Hand, Foot & Mouth Disease | — | true | 511 |
| `Hand, Foot & Mouth Disease_Las Pinas` | Hand, Foot & Mouth Disease | — | **false** → excluded | 1 |
| `Acute Bloody Diarrhea` | Acute Bloody Diarrhea | — | true | 372 |
| `Covid-19` | COVID-19 | — | true | 367 — **new in 2026 file** |
| `Acute Viral Hepatitis` | Acute Viral Hepatitis | — | true | 140 |
| `Bacterial Meningitis` | Bacterial Meningitis | — | true | 128 |
| `Non Neonatal Tetanus`, `Non neonatal Tetanus` | Non-Neonatal Tetanus | — | true | 73 |
| `Rotavirus` | Rotavirus | — | true | 55 |
| `Acute Myelogic Encephalitis Syndrome` | Acute Encephalitis Syndrome | — | true | 40 — rolled up under parent AES per PIDSR |
| `Meningococcal Disease` | Meningococcal Disease | — | true | 27 |
| `Meningococcal Disease_Suspect` / `_Negative` / `_pending` | Meningococcal Disease | **Suspect / Negative / Pending** | true | 3 |
| `Meningococcemia`, `Meningococcemia_Notpque` | Meningococcal Disease | — | varies | 2 (1 out-of-city) |
| `Acute Encephalitis Syndrome` | Acute Encephalitis Syndrome | — | true | 17 |
| `Acute Flaccid Paralysis` | Acute Flaccid Paralysis | — | true | 17 |
| `Severe Acute Respiratory Syndrome` | Severe Acute Respiratory Syndrome | — | true | 14 |
| `Diptheria`, `Diphtheria` | Diphtheria | — | true | 15 — **spelling fix**, PIDSR canonical is "Diphtheria" |
| `Diptheria_Negative` | Diphtheria | **Negative** | true | 1 |
| `Rabies` | Rabies | — | true | 13 |
| `Acute Hemorrhagic Fever Syndrome` | Acute Hemorrhagic Fever Syndrome | — | true | 12 |
| `pertussis`, `Pertussis`, `pertussisS` | Pertussis | — | true | 18 — casing + `pertussisS` typo |
| `Pertussis_Suspect` | Pertussis | **Suspect** | true | 1 |
| `Malaria` | Malaria | — | true | 8 |
| `Adverse Event Following  Immunization` | Adverse Event Following Immunization | — | true | 7 — **double-space typo fix** |
| `Chikungunya Virus` | Chikungunya | — | true | 6 |
| `Chikungunya Virus_Suspect` | Chikungunya | **Suspect** | true | 1 |
| `Neonatal Tetanus` | Neonatal Tetanus | — | true | 6 — distinct from Non-Neonatal; do **not** merge |
| `Rubella` | Rubella | — | true | 6 |
| `Zika` | Zika Virus Disease | — | true | 2 |
| `Cholera` | Cholera | — | true | 1 |

Eight PIDSR-listed diseases with zero observed cases (Anthrax, Acute Hemorrhagic Conjunctivitis, etc.) are still seeded in `hmap_db.diseases` so the data-entry dropdown stays PIDSR-complete; they carry `alert_enabled=0` until the first case is encoded.

---

## 2. CASECLASS normalization

The raw `CASECLASS` column has 82 distinct values in the 2026 file, up from 64 in the 2023 file. The expansion is almost entirely on the measles classification side — CESU now records granular confirmation pathways (lab, clinical, epi-linked). PIDSR collapses these to the same `Confirmed` bucket for surveillance counts.

| Canonical | Maps from raw `CASECLASS` containing… | Example raw values |
|---|---|---|
| **Confirmed** | `confirmed`, `c`, `lab confirmed`, `laboratory confirmed`, `clinically confirmed`, `epi-linked`, `epi linked`, `positive` | `Confirmed`, `C`, `Lab Confirmed Measles`, `Clinically Confirmed`, `Epi-Linked`, `Epi-linked Confirmed Measles`, `Laboratory Confirmed(CV-A16)`, `Positive` |
| **Probable** | `probable`, `p`, any `probable-*` prefix | `Probable`, `P`, `Probable_Typidot` |
| **Suspect** | `suspect`, `s`, `suspected` (anywhere) | `Suspect`, `S`, `SUSpect`, `Suspected`, `Suspected Meningitis`, `Suspected case of HFMD` |
| **Compatible** | `compatible` (anywhere) — must run **before** Confirmed rules so `Measles Compatible/Suspect` doesn't get caught by the Suspect rule | `Compatible`, `Measles Compatible`, `Measles Compatible/Suspect` |
| **Discarded** | `discarded`, `d`, `non polio`, `non-polio`, `non measles`, `non-measles` | `Discarded`, `D`, `Discarded as Non-Measles`, `Discarded as Non-Polio`, `Non Polio` |
| **Negative** | `negative`, `positive-escherichia` (lab result, treated as Negative for the suspected disease) | `Negative`, `Positive-Escherichia Coli` |
| **Pending** | `pending`, blank/NaN, everything else | `Pending`, `PENDING`, NaN |

Rule order matters: Compatible runs before Confirmed (so `Measles Compatible/Suspect` lands in Compatible, not Suspect); Discarded runs before Confirmed (so `Discarded as Non-Measles` doesn't match "non…confirmed" patterns); Negative runs before Suspect; Suspect comes last among classification matches so single-letter `s` is checked after the others.

**Pre-fix vs. post-fix.** Before the rule expansion, ~2,000 cases that should have been `Confirmed` were landing in `Pending` because the normalizer didn't recognize `Lab Confirmed Measles`, `Clinically Confirmed`, or `Epi-Linked` as confirmation pathways. The current Confirmed count of 6,122 reflects that fix.

---

## 3. Outcome normalization

| Canonical | Raw |
|---|---|
| Alive | `A`, `a`, `Alive`, `ALIVE` |
| Died | `D` |
| Unknown | NaN / blank / unknown values |

In the 2026 file: 35,383 `A` + 35 `a` (case typo) = 35,418 Alive; 288 `D` Died. No Unknowns.

---

## 4. Barangay mapping

The 16 official Parañaque barangays (PSA / PhilGIS standard names):

Baclaran · B.F. Homes · Don Bosco · Don Galo · La Huerta · Marcelo Green Village · Merville · Moonwalk · San Antonio · San Dionisio · San Isidro · San Martin de Porres · Santo Niño · Sun Valley · Tambo · Vitalez

### Mapping table

| Raw `Barangay` string(s) | → canonical | Rows (2026 file) |
|---|---|---|
| `SAN DIONISIO`, `San Dionisio` | San Dionisio | 5,056 |
| `SAN ISIDRO` | San Isidro | 4,690 |
| `B. F. HOMES`, `B. F. Homes` | B.F. Homes | 3,846 |
| `SAN ANTONIO`, `San Antonio` | San Antonio | 3,797 |
| `MOONWALK`, `Moonwalk` | Moonwalk | 3,623 |
| `DON BOSCO`, `DONBOSCO`† | Don Bosco | 3,200 |
| `SANTO NI�O` | Santo Niño | 1,826 — **mojibake fix** |
| `SUN VALLEY`, `Sun Valley` | Sun Valley | 1,765 |
| `TAMBO` | Tambo | 1,610 |
| `MARCELO GREEN`, `MARCELO GREEN VILLAGE`† | Marcelo Green Village | 1,253 |
| `BACLARAN`, `Baclaran` | Baclaran | 1,180 |
| `MERVILLE` | Merville | 1,041 |
| `LA HUERTA` | La Huerta | 700 |
| `DON GALO`, `Don Galo`† | Don Galo | 683 |
| `SAN MARTIN DE PORRES` | San Martin de Porres | 652 |
| `VITALEZ` | Vitalez | 262 |
| `UNKNOWN`, `Unknown` | *(null)* — **excluded as `unknown_barangay`** | 522 |
| out-of-city aliases (see below) | *(null)* — **excluded as `out_of_city`** | varies |

† Aliases retained for backward compatibility with the 2023 file. The 2026 file no longer uses these forms.

### Out-of-city aliases (historical)

The 2023 file scattered cases across these non-Parañaque strings. The 2026 file removed almost all of them upstream, but the ETL still recognizes and excludes them defensively:

`NOT PQUE`, `not pque`, `LAS PIÑAS`, `LAS PINAS`, `TAGUIG`, `PASAY`, `TAMBO/PASAY`, `BICUTAN`, `WESTERN BICUTAN`, `DAANG HARI`, `BARANGAY 176`

Notes on a few:
- `DAANG HARI` is a road, not a barangay (Las Piñas / Bacoor boundary).
- `BICUTAN`, `WESTERN BICUTAN` are Taguig barangays sitting on the Parañaque border.
- `BARANGAY 176` is a Caloocan barangay number.
- `TAMBO/PASAY` is genuinely ambiguous; excluded under the precautionary principle rather than guessed at.

---

## 5. Decisions made (and why)

1. **Out-of-city referrals are excluded, not deleted.** They land in `hmap_db.excluded_cases` with the original raw values and a `reason` code. Ch.1 scope explicitly excludes adjacent-city cases from city-level analytics, but keeping them auditable lets the thesis defense cite exact row counts.
2. **Discarded cases are retained as `case_classification='Discarded'`**, not dropped. PIDSR practice keeps discarded cases for the surveillance denominator (test rate, false-positive rate). Forecast and threshold modules will filter to `Confirmed ∪ Probable` as appropriate.
3. **Epi-linked cases count as Confirmed.** PIDSR treats epidemiologically-linked cases (no lab confirmation, but linked to a confirmed case in time/place) as confirmed for outbreak counts. This adds ~600 rows to the Confirmed bucket.
4. **`Measles Compatible` is its own canonical class**, not folded into Confirmed or Suspect. PIDSR uses Compatible when a case meets the clinical case definition and lab is unavailable — operationally distinct from a confirmed case with positive lab.
5. **Diphtheria spelling, AEFI double-space, Pertussis casing** — silent fixes at ETL. The 2026 file added the correct `Diphtheria` spelling alongside the legacy `Diptheria` typo; both map to `DIP`.
6. **Acute Myelogic Encephalitis Syndrome** rolls up under Acute Encephalitis Syndrome. PIDSR's AES surveillance covers myelogic/encephalitic sub-syndromes under the same reportable code.
7. **Meningococcemia** rolls up under Meningococcal Disease for the same reason.
8. **Eight PIDSR diseases with zero observed cases** (Anthrax, Acute Hemorrhagic Conjunctivitis, etc.) are seeded with `alert_enabled=0`. They appear in the data-entry dropdown for completeness but don't trigger empty-threshold computations.

---

## 6. Downstream pipeline

✅ `hmap_db.cases` populated and reconciled (35,164 rows from 35,706 source).
✅ `hmap_db.diseases` seeded (29 PIDSR diseases; 21 observed, 8 zero-case).
✅ `hmap_db.barangays` seeded (16 Parañaque barangays).
✅ `hmap_db.excluded_cases` audit trail populated (542 rows, exact reason per row).

Next:
- `hmap_db.thresholds` — WHO EWARN weekly thresholds (mean + 2σ) per disease × morbidity week, computed from the 2018–2022 historical baseline. **Decision needed:** how to handle 2020–2021 COVID-era data sparsity (586 + 690 rows) within the baseline window.
- Prophet weekly-case forecasting model — dengue first, given 25.6k rows over 17 years.
- Random Forest barangay-risk classifier — labels derive from the thresholds table.
