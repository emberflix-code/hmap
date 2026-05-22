"""H-MAP ETL: PIDSR Registry → hmap_db.cases.

Loads docs/PIDSR Report YR 2023.xlsx (sheet `Registry`, 30,134 rows) into a remote
MySQL hmap_db, applying the normalization rules documented in docs/data_mappings.md.

Usage:
    cp ml/.env.example ml/.env       # then edit ml/.env with DB credentials
    python ml/etl_registry.py        # runs schema + seed + load + verify

Order of operations:
    1. Connect to MySQL using DB_HOST/DB_USER/DB_PASSWORD from ml/.env
    2. Run schema.sql (drops + recreates all hmap_db tables)
    3. Seed reference tables: diseases (28 PIDSR canonical), barangays (16 Parañaque)
    4. Read Registry sheet, normalize, insert cases + excluded_cases
    5. Print reconciliation: 30,134 = mapped + excluded

The script is idempotent: each run drops and recreates all tables, then reloads from
the Excel source. Safe to re-run after any change to the mappings.
"""

from __future__ import annotations

import argparse
import logging
import os
import re
import sys
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Iterable

import pandas as pd
from dotenv import load_dotenv

from geocode import geocode_case_address, GeocodeOutcome

try:
    import mysql.connector
    from mysql.connector import errorcode
except ImportError:
    print("Missing dependency: pip install mysql-connector-python", file=sys.stderr)
    sys.exit(1)

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
SCHEMA_SQL = HERE / "schema.sql"


def find_latest_registry() -> Path:
    """Pick the newest 'PIDSR Report YR NNNN.xlsx' from docs/.

    Sorts by the four-digit year embedded in the filename, not by mtime — keeps
    things deterministic when both files are present.
    """
    candidates = list((REPO / "docs").glob("PIDSR Report YR *.xlsx"))
    if not candidates:
        raise FileNotFoundError("No 'PIDSR Report YR *.xlsx' files in docs/")
    def year_of(p: Path) -> int:
        m = re.search(r"YR\s*(\d{4})", p.name)
        return int(m.group(1)) if m else 0
    return max(candidates, key=year_of)


REGISTRY_XLSX = find_latest_registry()

logging.basicConfig(
    level=os.getenv("ML_LOG_LEVEL", "info").upper(),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
log = logging.getLogger("hmap.etl")


# ─── Canonical reference data ────────────────────────────────────────────────

# 28 PIDSR-notifiable diseases. The 20 we observe in the Registry are flagged
# alert_enabled=1. The 8 unobserved are seeded so the dropdown is PIDSR-complete
# but stay alert_enabled=0 / forecast_enabled=0 until cases are encoded.
DISEASES_SEED: list[dict] = [
    # observed in Registry
    {"code": "DENGUE",  "name": "Dengue",                                "cat": "Category 2", "alert": 1, "forecast": 1, "order": 1},
    {"code": "ILI",     "name": "Influenza-Like Illness",                "cat": "Category 2", "alert": 1, "forecast": 1, "order": 2},
    {"code": "MEA",     "name": "Measles",                               "cat": "Category 1", "alert": 1, "forecast": 1, "order": 3},
    {"code": "TYP",     "name": "Typhoid Fever",                         "cat": "Category 2", "alert": 1, "forecast": 1, "order": 4},
    {"code": "LEP",     "name": "Leptospirosis",                         "cat": "Category 2", "alert": 1, "forecast": 1, "order": 5},
    {"code": "HFMD",    "name": "Hand, Foot & Mouth Disease",            "cat": "Category 2", "alert": 1, "forecast": 1, "order": 6},
    {"code": "ABD",     "name": "Acute Bloody Diarrhea",                 "cat": "Category 2", "alert": 1, "forecast": 0, "order": 7},
    {"code": "BMENG",   "name": "Bacterial Meningitis",                  "cat": "Category 1", "alert": 1, "forecast": 0, "order": 8},
    {"code": "AVH",     "name": "Acute Viral Hepatitis",                 "cat": "Category 2", "alert": 1, "forecast": 0, "order": 9},
    {"code": "NNT",     "name": "Non-Neonatal Tetanus",                  "cat": "Category 2", "alert": 1, "forecast": 0, "order": 10},
    {"code": "NT",      "name": "Neonatal Tetanus",                      "cat": "Category 1", "alert": 1, "forecast": 0, "order": 11},
    {"code": "ROTA",    "name": "Rotavirus",                             "cat": "Category 2", "alert": 1, "forecast": 0, "order": 12},
    {"code": "MENG",    "name": "Meningococcal Disease",                 "cat": "Category 1", "alert": 1, "forecast": 0, "order": 13},
    {"code": "AES",     "name": "Acute Encephalitis Syndrome",           "cat": "Category 1", "alert": 1, "forecast": 0, "order": 14},
    {"code": "AFP",     "name": "Acute Flaccid Paralysis",               "cat": "Category 1", "alert": 1, "forecast": 0, "order": 15},
    {"code": "DIP",     "name": "Diphtheria",                            "cat": "Category 1", "alert": 1, "forecast": 0, "order": 16},
    {"code": "AHFS",    "name": "Acute Hemorrhagic Fever Syndrome",      "cat": "Category 1", "alert": 1, "forecast": 0, "order": 17},
    {"code": "RAB",     "name": "Rabies",                                "cat": "Category 1", "alert": 1, "forecast": 0, "order": 18},
    {"code": "MAL",     "name": "Malaria",                               "cat": "Category 2", "alert": 1, "forecast": 0, "order": 19},
    {"code": "PER",     "name": "Pertussis",                             "cat": "Category 1", "alert": 1, "forecast": 0, "order": 20},
    {"code": "AEFI",    "name": "Adverse Event Following Immunization",  "cat": "Category 1", "alert": 1, "forecast": 0, "order": 21},
    {"code": "RUB",     "name": "Rubella",                               "cat": "Category 1", "alert": 1, "forecast": 0, "order": 22},
    {"code": "CHK",     "name": "Chikungunya",                           "cat": "Category 2", "alert": 1, "forecast": 0, "order": 23},
    {"code": "SARS",    "name": "Severe Acute Respiratory Syndrome",     "cat": "Category 1", "alert": 1, "forecast": 0, "order": 24},
    {"code": "ZIKA",    "name": "Zika Virus Disease",                    "cat": "Category 2", "alert": 1, "forecast": 0, "order": 25},
    {"code": "CHO",     "name": "Cholera",                               "cat": "Category 1", "alert": 1, "forecast": 0, "order": 26},
    {"code": "COVID",   "name": "COVID-19",                              "cat": "Category 1", "alert": 1, "forecast": 0, "order": 27},
    # PIDSR-listed but not seen in Registry — kept so dropdown is complete
    {"code": "ANT",     "name": "Anthrax",                               "cat": "Category 1", "alert": 0, "forecast": 0, "order": 28},
    {"code": "AHC",     "name": "Acute Hemorrhagic Conjunctivitis",      "cat": "Category 2", "alert": 0, "forecast": 0, "order": 29},
]

# 16 official Parañaque barangays. Centroid lat/lng can be populated later from
# PhilGIS shapefile; ETL doesn't need them for case loading.
BARANGAYS_SEED: list[dict] = [
    {"name": "Baclaran",              "district": 1},
    {"name": "B.F. Homes",            "district": 2},
    {"name": "Don Bosco",             "district": 2},
    {"name": "Don Galo",              "district": 1},
    {"name": "La Huerta",             "district": 1},
    {"name": "Marcelo Green Village", "district": 2},
    {"name": "Merville",              "district": 2},
    {"name": "Moonwalk",              "district": 2},
    {"name": "San Antonio",           "district": 1},
    {"name": "San Dionisio",          "district": 1},
    {"name": "San Isidro",            "district": 1},
    {"name": "San Martin de Porres",  "district": 2},
    {"name": "Santo Niño",            "district": 1},
    {"name": "Sun Valley",            "district": 2},
    {"name": "Tambo",                 "district": 1},
    {"name": "Vitalez",               "district": 1},
]


# ─── Normalization rules (from docs/data_mappings.md) ────────────────────────

# Disease string → (canonical_code, classification_override or None, is_paranaque_resident)
# When classification_override is None, ETL uses the raw CASECLASS column.
# When False is in slot 3, the row is routed to excluded_cases as out_of_city.
DISEASE_MAP: dict[str, tuple[str, str | None, bool]] = {
    # Dengue
    "dengue":                              ("DENGUE", None, True),
    "dengue_not pque":                     ("DENGUE", None, False),
    "dengue_not resident":                 ("DENGUE", None, False),
    "dengue_not admitted":                 ("DENGUE", None, False),
    "dengue_muntinlupa":                   ("DENGUE", None, False),
    "dengue_pasay":                        ("DENGUE", None, False),
    "dengue_not pque_las piñas":           ("DENGUE", None, False),
    # Measles
    "measles":                             ("MEA", None,           True),
    "measles_suspect":                     ("MEA", "Suspect",      True),
    "measles suspect":                     ("MEA", "Suspect",      True),
    "measles_suspect_pending":             ("MEA", "Pending",      True),
    "measles_discarded":                   ("MEA", "Discarded",    True),
    "measles compatible":                  ("MEA", "Compatible",   True),
    "measles - negative":                  ("MEA", "Negative",     True),
    "measles negative":                    ("MEA", "Negative",     True),
    "measles - pending":                   ("MEA", "Pending",      True),
    "measles_not pque":                    ("MEA", None,           False),
    "measles_las pinas":                   ("MEA", None,           False),
    "measles_muntinlupa":                  ("MEA", None,           False),
    "measles_no pque":                     ("MEA", None,           False),
    # ILI
    "influenza like illness":              ("ILI", None, True),
    # Typhoid
    "typhoid fever":                       ("TYP", None, True),
    # Lepto
    "leptospirosis":                       ("LEP", None, True),
    # HFMD
    "hand, foot & mouth disease":             ("HFMD", None, True),
    "hand, foot & mouth disease_las pinas":   ("HFMD", None, False),
    # ABD
    "acute bloody diarrhea":               ("ABD", None, True),
    # Bacterial Meningitis
    "bacterial meningitis":                ("BMENG", None, True),
    "bacterial meningitis_not pque":       ("BMENG", None, False),
    # AVH
    "acute viral hepatitis":               ("AVH", None, True),
    # Tetanus
    "non neonatal tetanus":                ("NNT", None, True),
    "neonatal tetanus":                    ("NT",  None, True),
    # Rotavirus
    "rotavirus":                           ("ROTA", None, True),
    # Meningococcal
    "meningococcal disease":               ("MENG", None,        True),
    "meningococcal disease_suspect":       ("MENG", "Suspect",   True),
    "meningococcal disease_negative":      ("MENG", "Negative",  True),
    "meningococcal disease_pending":       ("MENG", "Pending",   True),
    "meningococcemia":                     ("MENG", None,        True),
    "meningococcemia_notpque":             ("MENG", None,        False),
    # AES
    "acute encephalitis syndrome":             ("AES", None, True),
    "acute myelogic encephalitis syndrome":    ("AES", None, True),
    # AFP
    "acute flaccid paralysis":             ("AFP", None, True),
    # Diphtheria (was misspelled "Diptheria" in Registry)
    "diphtheria":                          ("DIP", None,       True),
    "diphtheria_negative":                 ("DIP", "Negative", True),
    # AHFS
    "acute hemorrhagic fever syndrome":     ("AHFS", None, True),
    # Rabies
    "rabies":                              ("RAB", None, True),
    # Malaria
    "malaria":                             ("MAL", None, True),
    # Pertussis (including the "pertussisS" typo, handled post-normalization)
    "pertussis":                           ("PER", None,      True),
    "pertussis_suspect":                   ("PER", "Suspect", True),
    # AEFI
    "adverse event following immunization":  ("AEFI", None, True),
    # Rubella
    "rubella":                             ("RUB", None, True),
    # Chikungunya
    "chikungunya":                         ("CHK", None,      True),
    "chikungunya virus":                   ("CHK", None,      True),
    "chikungunya virus_suspect":           ("CHK", "Suspect", True),
    # SARS
    "severe acute respiratory syndrome":   ("SARS", None, True),
    # Zika
    "zika":                                ("ZIKA", None, True),
    # Cholera
    "cholera":                             ("CHO", None, True),
    # COVID-19 (added in 2026 file; PIDSR added as notifiable post-pandemic)
    "covid-19":                            ("COVID", None, True),
    "covid 19":                            ("COVID", None, True),
    "covid19":                             ("COVID", None, True),
}

# Barangay raw string → canonical name (or None to mark for exclusion)
BARANGAY_MAP: dict[str, str | None] = {
    "san dionisio":              "San Dionisio",
    "san isidro":                "San Isidro",
    "san antonio":               "San Antonio",
    "b. f. homes":               "B.F. Homes",
    "moonwalk":                  "Moonwalk",
    "don bosco":                 "Don Bosco",
    "donbosco":                  "Don Bosco",
    "santo niño":                "Santo Niño",
    "sun valley":                "Sun Valley",
    "tambo":                     "Tambo",
    "marcelo green village":     "Marcelo Green Village",
    "marcelo green":             "Marcelo Green Village",
    "baclaran":                  "Baclaran",
    "merville":                  "Merville",
    "don galo":                  "Don Galo",
    "la huerta":                 "La Huerta",
    "san martin de porres":      "San Martin de Porres",
    "vitalez":                   "Vitalez",
    # excluded — out of city
    "not pque":           None,
    "las piñas":          None,
    "las pinas":          None,
    "taguig":             None,
    "pasay":              None,
    "tambo/pasay":        None,
    "bicutan":            None,
    "western bicutan":    None,
    "daang hari":         None,
    "barangay 176":       None,
    # excluded — unknown
    "unknown":            None,
}
EXCLUDE_AS_UNKNOWN = {"unknown"}  # rest of "not in 16" → out_of_city
OUT_OF_CITY_BARANGAYS = {
    "not pque", "las piñas", "las pinas", "taguig", "pasay",
    "tambo/pasay", "bicutan", "western bicutan", "daang hari", "barangay 176",
}

# Case classification raw → canonical
def normalize_caseclass(raw: str | None, override: str | None) -> str:
    """Collapse CESU's free-text classifications to PIDSR canonical 7-tuple.

    The 2026 file has 82 distinct raw CASECLASS values. Rules below are ordered
    most-specific first; "Compatible" must come before the generic Confirmed
    rules because "Measles Compatible" is its own PIDSR class.
    """
    if override:
        return override
    if raw is None or (isinstance(raw, float) and pd.isna(raw)):
        return "Pending"
    s = str(raw).strip().lower()
    if s in {"", "nan"}:
        return "Pending"

    # --- Compatible (PIDSR: clinically compatible, lab-unavailable) ---
    if "compatible" in s:
        return "Compatible"

    # --- Discarded (includes AFP "Non Polio" rule-out and Measles "Non-Measles") ---
    if (s.startswith("discarded")
            or s == "d"
            or "non polio" in s
            or "non-polio" in s
            or "non measles" in s
            or "non-measles" in s):
        return "Discarded"

    # --- Negative (lab-negative for the suspected disease) ---
    if s.startswith("negative") or "positive-escherichia" in s:
        return "Negative"

    # --- Confirmed (lab, clinically, or epi-linked confirmation) ---
    # PIDSR treats "epi-linked confirmed" cases as Confirmed for surveillance counts.
    if (s.startswith("confirmed")
            or s == "c"
            or "lab confirmed" in s
            or "laboratory confirmed" in s
            or "clinically confirmed" in s
            or "epi-linked" in s
            or "epi linked" in s
            or s == "positive"):
        return "Confirmed"

    # --- Probable ---
    if s.startswith("probable") or s == "p":
        return "Probable"

    # --- Suspect ---
    if (s.startswith("suspect")
            or s == "s"
            or "suspected" in s):
        return "Suspect"

    # --- Pending (explicit) ---
    if s.startswith("pending"):
        return "Pending"

    return "Pending"

OUTCOME_MAP = {"A": "Alive", "a": "Alive", "ALIVE": "Alive", "Alive": "Alive", "D": "Died"}
SEX_MAP = {"M": "Male", "F": "Female", "m": "Male", "f": "Female"}


# ─── Mojibake fix ────────────────────────────────────────────────────────────

def fix_mojibake(s: str | None) -> str | None:
    """Restore Ñ in strings that lost it during a bad encoding round-trip."""
    if s is None or not isinstance(s, str):
        return s
    return s.replace("�", "Ñ").replace("ñ", "ñ")  # second is a no-op safety


def norm_disease_key(raw: str) -> str:
    """Lowercase + collapse double-spaces + fix mojibake + strip typos."""
    s = fix_mojibake(raw).strip().lower()
    s = re.sub(r"\s+", " ", s)
    # Diptheria → Diphtheria (canonical PIDSR spelling)
    s = s.replace("diptheria", "diphtheria")
    # "pertussisS" typo
    s = s.replace("pertussiss", "pertussis")
    return s


def safe_str(v) -> str | None:
    """pandas NaN / None → SQL NULL. Real values → str()."""
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return None
    return str(v)


def safe_int(v) -> int | None:
    if v is None or pd.isna(v):
        return None
    try:
        return int(v)
    except (TypeError, ValueError):
        return None


def norm_barangay_key(raw: str | None) -> str | None:
    if raw is None or not isinstance(raw, str):
        return None
    s = fix_mojibake(raw).strip().lower()
    s = re.sub(r"\s+", " ", s)
    return s


# ─── DB connection ───────────────────────────────────────────────────────────

@dataclass
class DbConfig:
    host: str
    port: int
    user: str
    password: str
    database: str

    @classmethod
    def from_env(cls) -> "DbConfig":
        load_dotenv(HERE / ".env")
        missing = [k for k in ("DB_HOST", "DB_USER", "DB_PASSWORD") if not os.getenv(k)]
        if missing:
            print(
                f"ERROR: missing env var(s) {missing}. "
                f"Copy ml/.env.example to ml/.env and fill in the values.",
                file=sys.stderr,
            )
            sys.exit(2)
        return cls(
            host=os.environ["DB_HOST"],
            port=int(os.getenv("DB_PORT", "3306")),
            user=os.environ["DB_USER"],
            password=os.environ["DB_PASSWORD"],
            database=os.getenv("DB_NAME", "hmap_db"),
        )


def connect_server(cfg: DbConfig):
    """Connect without selecting a database — used for CREATE DATABASE."""
    return mysql.connector.connect(
        host=cfg.host, port=cfg.port, user=cfg.user, password=cfg.password,
        charset="utf8mb4", use_unicode=True,
    )

def connect_db(cfg: DbConfig):
    """Connect with the target database selected."""
    return mysql.connector.connect(
        host=cfg.host, port=cfg.port, user=cfg.user, password=cfg.password,
        database=cfg.database, charset="utf8mb4", use_unicode=True,
    )


def run_schema(cfg: DbConfig) -> None:
    sql = SCHEMA_SQL.read_text(encoding="utf-8")
    # Execute via two cursors: server-level for CREATE DATABASE, db-level for the rest.
    conn = connect_server(cfg)
    try:
        cur = conn.cursor()
        # Split out the CREATE DATABASE + USE statements and run them first.
        for stmt in _split_sql(sql):
            cur.execute(stmt)
        conn.commit()
        log.info("schema applied to %s@%s", cfg.database, cfg.host)
    finally:
        conn.close()


def _split_sql(sql: str) -> Iterable[str]:
    """Split a multi-statement SQL script on `;` while respecting `--` comments."""
    out, cur = [], []
    for line in sql.splitlines():
        if line.strip().startswith("--") or not line.strip():
            continue
        cur.append(line)
        if line.rstrip().endswith(";"):
            stmt = "\n".join(cur).rstrip().rstrip(";").strip()
            if stmt:
                out.append(stmt)
            cur = []
    if cur:
        tail = "\n".join(cur).strip().rstrip(";")
        if tail:
            out.append(tail)
    return out


# ─── Seed reference tables ───────────────────────────────────────────────────

def seed_diseases(conn) -> dict[str, int]:
    cur = conn.cursor()
    cur.executemany(
        """INSERT INTO diseases
               (disease_code, disease_name, disease_category, alert_enabled, forecast_enabled, display_order)
           VALUES (%(code)s, %(name)s, %(cat)s, %(alert)s, %(forecast)s, %(order)s)""",
        DISEASES_SEED,
    )
    conn.commit()
    cur.execute("SELECT disease_id, disease_code FROM diseases")
    code_to_id = {code: did for did, code in cur.fetchall()}
    log.info("seeded %d diseases", len(code_to_id))
    return code_to_id


def seed_barangays(conn) -> dict[str, int]:
    cur = conn.cursor()
    cur.executemany(
        "INSERT INTO barangays (barangay_name, district) VALUES (%(name)s, %(district)s)",
        BARANGAYS_SEED,
    )
    conn.commit()
    cur.execute("SELECT barangay_id, barangay_name FROM barangays")
    name_to_id = {name: bid for bid, name in cur.fetchall()}
    log.info("seeded %d barangays", len(name_to_id))
    return name_to_id


# ─── Load cases ──────────────────────────────────────────────────────────────

def age_to_group(age: float | None) -> str | None:
    if age is None or pd.isna(age):
        return None
    a = int(age)
    if a < 5:   return "0-4"
    if a < 10:  return "5-9"
    if a < 15:  return "10-14"
    if a < 20:  return "15-19"
    if a < 60:  return "20-59"
    return "60+"


def to_date(v) -> date | None:
    if v is None or pd.isna(v):
        return None
    if isinstance(v, datetime):
        return v.date()
    if isinstance(v, date):
        return v
    try:
        return pd.to_datetime(v).date()
    except Exception:
        return None


@dataclass
class CaseAddress:
    """Per-case address payload captured during normalization, used by the
    post-insert geocoding pass. case_id is filled in after rows are inserted
    (auto-increment values from cursor.lastrowid)."""
    disease_code: str            # canonical PIDSR code (used for --pilot dengue filter)
    morbidity_year: int
    raw_street_purok: str | None
    raw_barangay: str             # canonical barangay name, post-mapping
    case_id: int | None = None    # filled after insert


def load_cases(conn, code_to_id: dict[str, int], bgy_to_id: dict[str, int]
                ) -> tuple[int, int, int, list[CaseAddress]]:
    log.info("reading %s", REGISTRY_XLSX.name)
    df = pd.read_excel(REGISTRY_XLSX, sheet_name="Registry")
    log.info("registry has %d rows", len(df))

    cases_rows: list[tuple] = []
    excluded_rows: list[tuple] = []
    unmapped_diseases: dict[str, int] = {}
    # Per-loaded-case address metadata, parallel-indexed to cases_rows so we
    # can pair each row with its case_id after the executemany insert
    addr_meta: list[CaseAddress] = []

    for _, r in df.iterrows():
        raw_disease = r["Disease"]
        raw_bgy = r["Barangay"]
        raw_caseclass = r.get("CASECLASS")
        raw_street_purok = r.get("StreetPurok")
        year = r.get("Year")
        mweek = r.get("MorbidityWeek")
        mmonth = r.get("MorbidityMonth")
        full_name = r.get("FullName")

        def excluded(reason: str, note: str) -> tuple:
            return (
                safe_str(raw_disease),
                safe_str(raw_bgy),
                safe_str(raw_caseclass),
                safe_int(year),
                safe_int(mweek),
                safe_str(full_name),
                reason,
                note,
            )

        # --- map disease ---
        if not isinstance(raw_disease, str):
            excluded_rows.append(excluded("invalid_data", "non-string disease"))
            continue
        dkey = norm_disease_key(raw_disease)
        mapping = DISEASE_MAP.get(dkey)
        if mapping is None:
            unmapped_diseases[raw_disease] = unmapped_diseases.get(raw_disease, 0) + 1
            excluded_rows.append(excluded("invalid_data", f"unmapped disease: {raw_disease!r}"))
            continue
        disease_code, class_override, is_paranaque = mapping

        if not is_paranaque:
            excluded_rows.append(excluded("out_of_city", "out-of-city per disease string"))
            continue

        # --- map barangay ---
        bkey = norm_barangay_key(raw_bgy)
        if bkey is None or bkey == "" or bkey == "nan":
            excluded_rows.append(excluded("unknown_barangay", "null/blank barangay"))
            continue
        if bkey in EXCLUDE_AS_UNKNOWN:
            excluded_rows.append(excluded("unknown_barangay", "explicit UNKNOWN"))
            continue
        if bkey in OUT_OF_CITY_BARANGAYS:
            excluded_rows.append(excluded("out_of_city", f"out-of-city barangay: {raw_bgy!r}"))
            continue
        canonical_bgy = BARANGAY_MAP.get(bkey)
        if canonical_bgy is None:
            excluded_rows.append(excluded("unknown_barangay", f"unmapped barangay: {raw_bgy!r}"))
            continue
        barangay_id = bgy_to_id.get(canonical_bgy)
        if barangay_id is None:
            excluded_rows.append(excluded("invalid_data", f"barangay seed mismatch: {canonical_bgy!r}"))
            continue

        # --- validate week/year ---
        if pd.isna(year) or pd.isna(mweek):
            excluded_rows.append(excluded("invalid_data", "missing year or morbidity week"))
            continue

        case_classification = normalize_caseclass(raw_caseclass, class_override)
        age_val = r.get("AgeYears")
        age_int = int(age_val) if pd.notna(age_val) and age_val >= 0 and age_val < 200 else None
        age_grp = age_to_group(age_val)
        sex = SEX_MAP.get(str(r.get("Sex", "")).strip()) if pd.notna(r.get("Sex")) else None
        outcome = OUTCOME_MAP.get(str(r.get("Outcome", "")).strip()) if pd.notna(r.get("Outcome")) else None

        cases_rows.append((
            code_to_id[disease_code],
            case_classification,
            to_date(r.get("DOnset")),
            to_date(r.get("DAdmit")),
            None,  # date_reported not in Registry
            barangay_id,
            None,  # facility_id — facilities table not yet populated
            age_int,
            age_grp,
            sex,
            outcome or "Unknown",
            int(mweek),
            int(mmonth) if pd.notna(mmonth) else None,
            int(year),
        ))
        addr_meta.append(CaseAddress(
            disease_code=disease_code,
            morbidity_year=int(year),
            raw_street_purok=safe_str(raw_street_purok),
            raw_barangay=canonical_bgy,
        ))

    log.info("normalized: %d to cases, %d to excluded_cases", len(cases_rows), len(excluded_rows))
    if unmapped_diseases:
        log.warning("unmapped disease strings (excluded as invalid_data): %s", unmapped_diseases)

    cur = conn.cursor()
    cur.executemany(
        """INSERT INTO cases
               (disease_id, case_classification, date_onset, date_admitted, date_reported,
                barangay_id, facility_id, age, age_group, sex, outcome,
                morbidity_week, morbidity_month, morbidity_year)
           VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
        cases_rows,
    )
    # MySQL guarantees consecutive auto_increment values from a single executemany
    # call (innodb_autoinc_lock_mode in {1,2}, both default-safe). lastrowid
    # points to the FIRST inserted row, not the last (per MySQL Connector docs).
    # https://dev.mysql.com/doc/connector-python/en/connector-python-api-mysqlcursor-lastrowid.html
    first_id = cur.lastrowid
    for i, meta in enumerate(addr_meta):
        meta.case_id = first_id + i

    cur.executemany(
        """INSERT INTO excluded_cases
               (raw_disease, raw_barangay, raw_caseclass, raw_year, raw_morbidity_week,
                raw_full_name, exclusion_reason, exclusion_notes)
           VALUES (%s,%s,%s,%s,%s,%s,%s,%s)""",
        excluded_rows,
    )
    conn.commit()
    return len(df), len(cases_rows), len(excluded_rows), addr_meta


# ─── Geocode pass ────────────────────────────────────────────────────────────

@dataclass
class GeocodeStats:
    attempted: int = 0
    from_cache: int = 0
    from_api: int = 0
    by_source: dict[str, int] = None  # type: ignore[assignment]

    def __post_init__(self):
        if self.by_source is None:
            self.by_source = {}


def geocode_addresses(conn, addr_meta: list[CaseAddress], scope: str,
                       user_agent: str, pilot_year: int | None = None) -> GeocodeStats:
    """Geocode the StreetPurok addresses for loaded cases.

    scope:
        "dengue"      — only diseases where disease_code == DENGUE
        "all"         — every case with a non-blank StreetPurok
        "none"        — skip geocoding entirely (insert no case_addresses rows)

    pilot_year:
        If set, further restrict to cases in this morbidity_year (e.g. 2024
        for the ~1,500-row pilot validation before the full backfill).

    Writes one row to case_addresses per attempted case. The cache survives
    across ETL runs (see schema.sql), so re-runs only hit Nominatim for
    addresses not seen before.
    """
    stats = GeocodeStats()
    if scope == "none":
        log.info("geocoding scope=none; skipping case_addresses population")
        return stats

    # Purge any cached `failed` entries so they get retried this run. The
    # geocoder no longer caches new failures (transient errors aren't trusted
    # as permanent), but earlier ETL runs may have written `failed` rows
    # before that fix landed. Leaving them in cache would lock in false
    # negatives — the pre-fix pilot had ~28% bogus `failed` from rate limits.
    cur = conn.cursor()
    cur.execute("DELETE FROM geocode_cache WHERE geocode_source = 'failed'")
    purged = cur.rowcount
    conn.commit()
    cur.close()
    if purged > 0:
        log.info("purged %d stale `failed` cache entries; they will be retried", purged)

    # Filter the metadata list
    targets = addr_meta
    if scope == "dengue":
        targets = [m for m in targets if m.disease_code == "DENGUE"]
    if pilot_year is not None:
        targets = [m for m in targets if m.morbidity_year == pilot_year]
    # A blank StreetPurok can't be geocoded, but we still record `failed` for it
    # so case_addresses has 1:1 coverage with the targeted cases.

    log.info("geocoding %d cases (scope=%s%s)",
             len(targets), scope,
             f", pilot_year={pilot_year}" if pilot_year else "")

    cur = conn.cursor()
    last_log = 0
    for i, meta in enumerate(targets):
        if meta.case_id is None or not meta.raw_street_purok:
            # Record a `failed` row so case_addresses is complete
            cur.execute(
                """INSERT INTO case_addresses
                       (case_id, raw_street_purok, geocode_source)
                   VALUES (%s, %s, 'failed')""",
                (meta.case_id, (meta.raw_street_purok or "")[:255]),
            )
            stats.attempted += 1
            stats.by_source["failed"] = stats.by_source.get("failed", 0) + 1
            continue

        outcome, from_cache = geocode_case_address(
            conn, meta.raw_street_purok, meta.raw_barangay, user_agent
        )
        stats.attempted += 1
        if from_cache:
            stats.from_cache += 1
        else:
            stats.from_api += 1
        stats.by_source[outcome.geocode_source] = (
            stats.by_source.get(outcome.geocode_source, 0) + 1
        )

        cur.execute(
            """INSERT INTO case_addresses
                   (case_id, raw_street_purok, case_lat, case_lng,
                    geocode_source, geocode_query, geocode_formatted)
               VALUES (%s, %s, %s, %s, %s, %s, %s)""",
            (
                meta.case_id,
                meta.raw_street_purok[:255],
                outcome.lat,
                outcome.lng,
                outcome.geocode_source,
                (outcome.geocode_query or "")[:255] or None,
                (outcome.formatted or "")[:255] or None,
            ),
        )

        # Progress log every 100 cases or every 30s, whichever comes first.
        # The API path takes ~1.1s per call (rate limit), cache path is instant.
        if (i + 1) % 100 == 0 or (i + 1) == len(targets):
            log.info("  geocode progress: %d/%d (cache=%d, api=%d)",
                     i + 1, len(targets), stats.from_cache, stats.from_api)
        # Commit in batches so progress is durable if the run is interrupted
        if (i + 1) % 50 == 0:
            conn.commit()
    conn.commit()
    cur.close()
    return stats


# ─── Verify / reconcile ──────────────────────────────────────────────────────

def verify_geocode(conn, stats: GeocodeStats) -> None:
    """Print a coverage report for the case_addresses table after geocoding."""
    if stats.attempted == 0:
        return
    cur = conn.cursor()
    cur.execute(
        """SELECT geocode_source, COUNT(*) FROM case_addresses
            GROUP BY geocode_source"""
    )
    by_source_db = dict(cur.fetchall())
    cur.execute("SELECT COUNT(*) FROM geocode_cache")
    cache_size = cur.fetchone()[0]
    cur.close()

    bar = "=" * 67
    print()
    print(bar)
    print("  Geocoding Coverage")
    print(bar)
    print(f"  Attempted:                  {stats.attempted:>7,}")
    print(f"    From cache (instant):     {stats.from_cache:>7,}")
    print(f"    From Nominatim API:       {stats.from_api:>7,}")
    print(f"  geocode_cache total size:   {cache_size:>7,}")
    print()
    print("  case_addresses by geocode_source:")
    usable = 0
    for source, n in sorted(by_source_db.items()):
        marker = " (usable for clusters)" if source in (
            "nominatim_street", "nominatim_subd", "manual_pin"
        ) else ""
        if source in ("nominatim_street", "nominatim_subd", "manual_pin"):
            usable += n
        print(f"    {source:<28} {n:>7,}{marker}")
    pct_usable = (usable / stats.attempted * 100) if stats.attempted else 0
    print()
    print(f"  Usable for 200m clustering: {usable:>7,}  ({pct_usable:.1f}%)")
    print(bar)


def verify(conn, total_registry: int, loaded: int, excluded: int) -> None:
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM cases")
    db_cases = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM excluded_cases")
    db_excluded = cur.fetchone()[0]
    cur.execute("SELECT exclusion_reason, COUNT(*) FROM excluded_cases GROUP BY exclusion_reason")
    by_reason = dict(cur.fetchall())
    cur.execute(
        """SELECT d.disease_name, COUNT(*) AS n
             FROM cases c JOIN diseases d ON d.disease_id = c.disease_id
            GROUP BY d.disease_name ORDER BY n DESC LIMIT 10"""
    )
    top_diseases = cur.fetchall()
    cur.execute(
        """SELECT b.barangay_name, COUNT(*) AS n
             FROM cases c JOIN barangays b ON b.barangay_id = c.barangay_id
            GROUP BY b.barangay_name ORDER BY n DESC"""
    )
    by_barangay = cur.fetchall()

    bar = "=" * 67
    print()
    print(bar)
    print("  H-MAP ETL Reconciliation")
    print(bar)
    print(f"  Registry source rows:          {total_registry:>7,}")
    print(f"  -> cases (loaded):             {db_cases:>7,}")
    print(f"  -> excluded_cases (audited):   {db_excluded:>7,}")
    print(f"  Sum:                           {db_cases + db_excluded:>7,}")
    match = "MATCH" if db_cases + db_excluded == total_registry else "MISMATCH"
    print(f"  Reconciliation:                {match}")
    print()
    print("  Excluded by reason:")
    for reason, n in by_reason.items():
        print(f"    {reason:<20} {n:>5,}")
    print()
    print("  Top 10 diseases loaded:")
    for name, n in top_diseases:
        safe_name = name.encode("ascii", "replace").decode("ascii")
        print(f"    {safe_name:<40} {n:>6,}")
    print()
    print("  All 16 barangays:")
    for name, n in by_barangay:
        safe_name = name.encode("ascii", "replace").decode("ascii")
        print(f"    {safe_name:<28} {n:>6,}")
    print(bar)


# ─── Entry point ─────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="H-MAP ETL: PIDSR Registry → hmap_db. Optionally geocodes addresses."
    )
    parser.add_argument(
        "--geocode", choices=("dengue", "all", "none"), default="dengue",
        help="Which cases to geocode after loading (default: dengue). "
             "Set to 'none' to skip the geocoding pass entirely.",
    )
    parser.add_argument(
        "--pilot-year", type=int, default=None,
        help="If set, only geocode cases in this morbidity_year (e.g. 2024 "
             "for a ~1,500-row pilot before committing to a full backfill).",
    )
    args = parser.parse_args()

    if not REGISTRY_XLSX.exists():
        print(f"ERROR: {REGISTRY_XLSX} not found", file=sys.stderr)
        sys.exit(2)
    if not SCHEMA_SQL.exists():
        print(f"ERROR: {SCHEMA_SQL} not found", file=sys.stderr)
        sys.exit(2)

    cfg = DbConfig.from_env()
    user_agent = os.getenv("NOMINATIM_USER_AGENT", "hmap-capstone").strip()
    log.info("connecting to %s@%s:%d (db=%s)", cfg.user, cfg.host, cfg.port, cfg.database)

    run_schema(cfg)

    conn = connect_db(cfg)
    try:
        code_to_id = seed_diseases(conn)
        bgy_to_id = seed_barangays(conn)
        total, loaded, excluded, addr_meta = load_cases(conn, code_to_id, bgy_to_id)
        verify(conn, total, loaded, excluded)

        geocode_stats = geocode_addresses(
            conn, addr_meta,
            scope=args.geocode,
            user_agent=user_agent,
            pilot_year=args.pilot_year,
        )
        verify_geocode(conn, geocode_stats)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
