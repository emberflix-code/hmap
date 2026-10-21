"""Encrypted database backups with checksums and test restorations (Ch.3 Module 9).

    python ml/backup_db.py create              # nightly (cron): dump, gzip, AES-256, log, prune
    python ml/backup_db.py verify              # weekly (cron): test-restore the latest backup
    python ml/backup_db.py verify --id 12      # test-restore a specific backup
    python ml/backup_db.py list                # recent backups and their verification status
    python ml/backup_db.py restore --id 12 --target hmap_db_recovered
    python ml/backup_db.py restore --id 12 --target hmap_db --overwrite-live   # real recovery

Each backup is `mysqldump --single-transaction` → gzip → `openssl enc
-aes-256-cbc -pbkdf2`, so it can also be restored by hand with standard tools
(see docs/BACKUP_AND_RESTORE.md). The plaintext dump only exists as a 0600
temporary file inside BACKUP_DIR and is deleted as soon as it is encrypted.

backup_log records each file's SHA-256, size, and per-table row counts.
`verify` recomputes the checksum, restores into RESTORE_TEST_DB, compares the
row count of every table, records the result, and empties the scratch
database again.

Configuration (ml/.env):
    BACKUP_DIR             default /var/backups/hmap
    BACKUP_KEY_FILE        default /etc/hmap/backup.key  (root/user1-only, 0600)
    BACKUP_RETENTION_DAYS  default 30
    RESTORE_TEST_DB        default <DB_NAME>_restore_test
    MYSQLDUMP_BIN / MYSQL_BIN / OPENSSL_BIN   default: found on PATH
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import mysql.connector
from dotenv import load_dotenv

HERE = Path(__file__).resolve().parent
load_dotenv(HERE / ".env")

DB = {
    "host": os.environ.get("DB_HOST", "127.0.0.1"),
    "port": int(os.environ.get("DB_PORT", "3306")),
    "user": os.environ["DB_USER"],
    "password": os.environ["DB_PASSWORD"],
    "database": os.environ.get("DB_NAME", "hmap_db"),
}
BACKUP_DIR = Path(os.environ.get("BACKUP_DIR", "/var/backups/hmap"))
KEY_FILE = Path(os.environ.get("BACKUP_KEY_FILE", "/etc/hmap/backup.key"))
RETENTION_DAYS = int(os.environ.get("BACKUP_RETENTION_DAYS", "30"))
RESTORE_TEST_DB = os.environ.get("RESTORE_TEST_DB", DB["database"] + "_restore_test")
MYSQLDUMP = os.environ.get("MYSQLDUMP_BIN") or "mysqldump"
MYSQL = os.environ.get("MYSQL_BIN") or "mysql"
OPENSSL = os.environ.get("OPENSSL_BIN") or "openssl"
CIPHER = ["-aes-256-cbc", "-pbkdf2", "-iter", "200000", "-salt"]


def connect(database: str):
    return mysql.connector.connect(host=DB["host"], port=DB["port"], user=DB["user"],
                                   password=DB["password"], database=database, charset="utf8mb4")


def client_options_file() -> str:
    """Credentials for mysqldump/mysql in a 0600 temp file, never on the command line."""
    fd, path = tempfile.mkstemp(prefix="hmap-my-", suffix=".cnf")
    with os.fdopen(fd, "w") as f:
        f.write(f"[client]\nhost={DB['host']}\nport={DB['port']}\nuser={DB['user']}\n"
                f"password=\"{DB['password']}\"\n")
    os.chmod(path, 0o600)
    return path


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def table_counts(database: str) -> dict:
    conn = connect(database)
    cur = conn.cursor()
    cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = %s "
                "AND table_type = 'BASE TABLE' ORDER BY table_name", (database,))
    counts = {}
    for (name,) in cur.fetchall():
        cur.execute(f"SELECT COUNT(*) FROM `{name}`")
        counts[name] = cur.fetchone()[0]
    conn.close()
    return counts


def require_key() -> None:
    if not KEY_FILE.exists():
        sys.exit(f"backup key not found at {KEY_FILE}; see docs/BACKUP_AND_RESTORE.md")


# ─── create ──────────────────────────────────────────────────────────────────

def cmd_create(_args) -> None:
    require_key()
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    started = datetime.now()
    name = f"{DB['database']}_{started:%Y%m%d_%H%M%S}.sql.gz.enc"
    enc_path = BACKUP_DIR / name
    plain_path = BACKUP_DIR / (name + ".partial")  # gzip'd dump, deleted after encryption

    conn = connect(DB["database"])
    cur = conn.cursor()
    cur.execute("INSERT INTO backup_log (started_at, file_name, status) VALUES (%s, %s, 'running')",
                (started, name))
    conn.commit()
    backup_id = cur.lastrowid

    opts = client_options_file()
    try:
        # backup_log changes during this very run, so it is left out of the check
        before = table_counts(DB["database"])
        before.pop("backup_log", None)
        fd = os.open(plain_path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "wb") as raw, gzip.GzipFile(fileobj=raw, mode="wb") as gz:
            dump = subprocess.Popen(
                [MYSQLDUMP, f"--defaults-extra-file={opts}", "--single-transaction", "--quick",
                 "--triggers", "--no-tablespaces", "--hex-blob",
                 "--default-character-set=utf8mb4", DB["database"]],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            shutil.copyfileobj(dump.stdout, gz)
            _, err = dump.communicate()
            if dump.returncode != 0:
                raise RuntimeError("mysqldump failed: " + err.decode(errors="replace").strip())
        # rows written while the dump ran make the exact count uncertain; for
        # those tables store [count before, count after] and accept the range
        after = table_counts(DB["database"])
        counts = {t: n if after.get(t) == n else sorted([n, after.get(t, n)])
                  for t, n in before.items()}
        subprocess.run([OPENSSL, "enc", *CIPHER, "-pass", f"file:{KEY_FILE}",
                        "-in", str(plain_path), "-out", str(enc_path)],
                       check=True, capture_output=True)
        os.chmod(enc_path, 0o600)
        digest, size = sha256(enc_path), enc_path.stat().st_size
        cur.execute("UPDATE backup_log SET finished_at = %s, status = 'success', sha256 = %s, "
                    "file_size_bytes = %s, table_row_counts = %s WHERE backup_id = %s",
                    (datetime.now(), digest, size, json.dumps(counts), backup_id))
        conn.commit()
        print(f"backup {backup_id} ok: {enc_path} ({size / 1048576:.1f} MB, sha256 {digest[:12]}…)")
    except Exception as e:
        enc_path.unlink(missing_ok=True)
        cur.execute("UPDATE backup_log SET finished_at = %s, status = 'failed', error = %s "
                    "WHERE backup_id = %s", (datetime.now(), str(e)[:2000], backup_id))
        conn.commit()
        raise
    finally:
        plain_path.unlink(missing_ok=True)
        os.unlink(opts)

    prune(cur, keep_id=backup_id)
    conn.commit()
    conn.close()


def prune(cur, keep_id: int) -> None:
    """Delete encrypted files older than the retention period; keep their log rows.
    The backup just made is never pruned, whatever the retention setting."""
    cutoff = datetime.now() - timedelta(days=RETENTION_DAYS)
    cur.execute("SELECT backup_id, file_name FROM backup_log WHERE status = 'success' "
                "AND deleted_at IS NULL AND started_at < %s AND backup_id <> %s",
                (cutoff, keep_id))
    for backup_id, name in cur.fetchall():
        (BACKUP_DIR / name).unlink(missing_ok=True)
        cur.execute("UPDATE backup_log SET deleted_at = %s WHERE backup_id = %s",
                    (datetime.now(), backup_id))
        print(f"pruned backup {backup_id} ({name}), older than {RETENTION_DAYS} days")


# ─── restore helpers ─────────────────────────────────────────────────────────

def drop_all_tables(database: str) -> None:
    conn = connect(database)
    cur = conn.cursor()
    cur.execute("SET FOREIGN_KEY_CHECKS = 0")
    cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = %s",
                (database,))
    for (name,) in cur.fetchall():
        cur.execute(f"DROP TABLE IF EXISTS `{name}`")
    conn.close()


def load_backup(row: dict, target_db: str) -> None:
    """Checksum, decrypt, gunzip, and load a backup into target_db (emptied first)."""
    require_key()
    path = BACKUP_DIR / row["file_name"]
    if not path.exists():
        raise RuntimeError(f"backup file missing: {path}")
    if sha256(path) != row["sha256"]:
        raise RuntimeError("checksum mismatch: the backup file was altered or damaged")

    drop_all_tables(target_db)
    opts = client_options_file()
    try:
        dec = subprocess.Popen([OPENSSL, "enc", "-d", *CIPHER, "-pass", f"file:{KEY_FILE}",
                                "-in", str(path)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        load = subprocess.Popen([MYSQL, f"--defaults-extra-file={opts}",
                                 "--default-character-set=utf8mb4", target_db],
                                stdin=subprocess.PIPE, stderr=subprocess.PIPE)
        try:
            with gzip.GzipFile(fileobj=dec.stdout) as gz:
                shutil.copyfileobj(gz, load.stdin)
        except OSError:
            load.kill()
            dec.kill()
            raise RuntimeError(f"could not decrypt with {KEY_FILE}: wrong key, or a damaged file")
        load.stdin.close()
        load_err = load.stderr.read()
        if load.wait() != 0:
            raise RuntimeError("mysql load failed: " + load_err.decode(errors="replace").strip())
        if dec.wait() != 0:
            raise RuntimeError("decryption failed: " + dec.stderr.read().decode(errors="replace"))
    finally:
        os.unlink(opts)


def get_row(backup_id: int | None) -> dict:
    conn = connect(DB["database"])
    cur = conn.cursor(dictionary=True)
    if backup_id is None:
        cur.execute("SELECT * FROM backup_log WHERE status = 'success' AND deleted_at IS NULL "
                    "ORDER BY started_at DESC LIMIT 1")
    else:
        cur.execute("SELECT * FROM backup_log WHERE backup_id = %s", (backup_id,))
    row = cur.fetchone()
    conn.close()
    if not row:
        sys.exit("no matching backup found")
    if row["status"] != "success":
        sys.exit(f"backup {row['backup_id']} has status {row['status']}; cannot restore it")
    return row


# ─── verify / restore / list ─────────────────────────────────────────────────

def cmd_verify(args) -> None:
    row = get_row(args.id)
    expected = json.loads(row["table_row_counts"])
    status, detail = "passed", ""
    try:
        load_backup(row, RESTORE_TEST_DB)
        restored = table_counts(RESTORE_TEST_DB)
        restored.pop("backup_log", None)
        def ok(t, n):
            got = restored.get(t)
            return got is not None and (n[0] <= got <= n[1] if isinstance(n, list) else got == n)

        diffs = [f"{t}: expected {n}, restored {restored.get(t)}"
                 for t, n in expected.items() if not ok(t, n)]
        missing = sorted(set(restored) - set(expected))
        if diffs or missing:
            status = "failed"
            detail = "; ".join(diffs + [f"unexpected table {t}" for t in missing])
        else:
            detail = f"{len(expected)} tables, {sum(restored.values())} rows matched"
    except Exception as e:
        status, detail = "failed", str(e)
    finally:
        # empty the scratch database so restored patient data does not linger
        try:
            drop_all_tables(RESTORE_TEST_DB)
        except Exception as e:  # noqa: BLE001 - report, but keep the verify result
            print(f"warning: could not empty {RESTORE_TEST_DB}: {e}")

    conn = connect(DB["database"])
    cur = conn.cursor()
    cur.execute("UPDATE backup_log SET verified_at = %s, verify_status = %s, verify_detail = %s "
                "WHERE backup_id = %s", (datetime.now(), status, detail[:2000], row["backup_id"]))
    conn.commit()
    conn.close()
    print(f"verify backup {row['backup_id']}: {status.upper()} ({detail})")
    if status != "passed":
        sys.exit(1)


def cmd_restore(args) -> None:
    if args.target == DB["database"] and not args.overwrite_live:
        sys.exit(f"refusing to overwrite the live database {args.target}; "
                 "restore into another database first, or pass --overwrite-live")
    row = get_row(args.id)
    load_backup(row, args.target)
    print(f"restored backup {row['backup_id']} ({row['file_name']}) into {args.target}")


def cmd_list(_args) -> None:
    conn = connect(DB["database"])
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT backup_id, started_at, status, file_size_bytes, verify_status, "
                "verified_at, deleted_at FROM backup_log ORDER BY started_at DESC LIMIT 20")
    for r in cur.fetchall():
        size = f"{(r['file_size_bytes'] or 0) / 1048576:.1f} MB"
        print(f"{r['backup_id']:>4}  {r['started_at']:%Y-%m-%d %H:%M}  {r['status']:<8} {size:>9}  "
              f"verify={r['verify_status'] or '-':<7} {'(file pruned)' if r['deleted_at'] else ''}")
    conn.close()


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = p.add_subparsers(dest="command", required=True)
    sub.add_parser("create").set_defaults(fn=cmd_create)
    v = sub.add_parser("verify")
    v.add_argument("--id", type=int, default=None)
    v.set_defaults(fn=cmd_verify)
    r = sub.add_parser("restore")
    r.add_argument("--id", type=int, required=True)
    r.add_argument("--target", required=True)
    r.add_argument("--overwrite-live", action="store_true")
    r.set_defaults(fn=cmd_restore)
    sub.add_parser("list").set_defaults(fn=cmd_list)
    args = p.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
