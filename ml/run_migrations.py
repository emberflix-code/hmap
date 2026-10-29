"""Applies ml/migrations/*.sql to one database, once each, in filename order.

Each migration declares the databases it may run against on a header line:

    -- targets: hmap_db, hmap_db_demo

and is skipped for any other database, so a demo-only script (for example
the patient-name scrub) can never run against production. Applied files are
recorded in schema_migrations, so re-running is safe.

Usage:
    python ml/run_migrations.py --db hmap_db_demo            # apply pending
    python ml/run_migrations.py --db hmap_db --dry-run       # list pending only
    python ml/run_migrations.py --db hmap_db --port 3307     # e.g. via SSH tunnel

After a fresh load of ml/schema.sql (e.g. by ml/etl_registry.py), the
schema already contains what the ALTER-style migrations add, so record those
as applied without running them, then apply the rest (which seed data):

    python ml/run_migrations.py --db hmap_db --mark-applied \\
        2026_10_21_single_case_trigger.sql 2026_10_31_user_roles_name.sql
    python ml/run_migrations.py --db hmap_db
"""

from __future__ import annotations

import argparse
import os
import re
from pathlib import Path

import mysql.connector
from dotenv import load_dotenv

HERE = Path(__file__).resolve().parent
MIGRATIONS = HERE / "migrations"


def targets_of(sql: str) -> set:
    m = re.search(r"^--\s*targets:\s*(.+)$", sql, re.M)
    return {t.strip() for t in m.group(1).split(",")} if m else set()


def statements(sql: str) -> list:
    """Split a migration into statements (no semicolons inside string literals)."""
    body = "\n".join(ln for ln in sql.splitlines() if not ln.lstrip().startswith("--"))
    return [s.strip() for s in body.split(";") if s.strip()]


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--db", required=True, help="database to migrate, e.g. hmap_db or hmap_db_demo")
    p.add_argument("--host", default=None)
    p.add_argument("--port", type=int, default=None)
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--mark-applied", nargs="+", metavar="FILE", default=None,
                   help="record these migration files as applied without running them "
                        "(for a database just built from the current schema.sql)")
    p.add_argument("--as", dest="as_name", default=None,
                   help="treat --db as this target name for the targets check "
                        "(for a renamed or test copy, e.g. --db test_copy --as hmap_db_demo)")
    args = p.parse_args()
    target_name = args.as_name or args.db

    load_dotenv(HERE / ".env")
    conn = mysql.connector.connect(
        host=args.host or os.environ["DB_HOST"],
        port=args.port or int(os.getenv("DB_PORT", "3306")),
        user=os.environ["DB_USER"], password=os.environ["DB_PASSWORD"],
        database=args.db, charset="utf8mb4", connection_timeout=20,
    )
    cur = conn.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS schema_migrations (
                       filename   VARCHAR(190) NOT NULL PRIMARY KEY,
                       applied_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP)""")
    if args.mark_applied:
        for name in args.mark_applied:
            if not (MIGRATIONS / name).exists():
                raise SystemExit(f"no such migration: {name}")
            cur.execute("INSERT IGNORE INTO schema_migrations (filename) VALUES (%s)", (name,))
            print(f"marked {name}")
        conn.commit()
        conn.close()
        return

    cur.execute("SELECT filename FROM schema_migrations")
    applied = {r[0] for r in cur.fetchall()}

    for path in sorted(MIGRATIONS.glob("*.sql")):
        sql = path.read_text(encoding="utf-8")
        targets = targets_of(sql)
        if target_name not in targets:
            print(f"skip   {path.name} (targets: {', '.join(sorted(targets)) or 'none declared'})")
            continue
        if path.name in applied:
            print(f"done   {path.name}")
            continue
        if args.dry_run:
            print(f"PENDING {path.name}")
            continue
        print(f"apply  {path.name}")
        for stmt in statements(sql):
            cur.execute(stmt)
            if cur.with_rows:
                for row in cur.fetchall():
                    print("         ", row)
        cur.execute("INSERT INTO schema_migrations (filename) VALUES (%s)", (path.name,))
        conn.commit()
    conn.close()


if __name__ == "__main__":
    main()
