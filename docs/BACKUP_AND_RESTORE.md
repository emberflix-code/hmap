# Backup and Restore Runbook

`ml/backup_db.py` makes nightly encrypted backups of `hmap_db`, test-restores
one every week, and records both in `backup_log`. Administrators see the
register under **Reports → Database backups**. Creating, verifying, and
restoring are done only from the server shell.

| What | How |
|---|---|
| Format | `mysqldump --single-transaction` → gzip → `openssl enc -aes-256-cbc -pbkdf2 -iter 200000` |
| Integrity | SHA-256 of each encrypted file, recomputed before every restore |
| Completeness | Row count of every table at backup time, compared after each test restore |
| Retention | 30 days of files (`BACKUP_RETENTION_DAYS`); log rows are kept permanently |
| Location | `/var/backups/hmap` (`BACKUP_DIR`), files mode 0600 |

The demo database (`hmap_db_demo`) holds only anonymized data and is rebuilt
from the anonymizer. It does not need backups.

---

## One-time setup (production server)

```bash
# 1. Table (also created by a fresh ml/schema.sql load)
cd /var/www/html/hmap
ml/.venv/bin/python ml/run_migrations.py --db hmap_db

# 2. Encryption key: random, readable only by the account that runs cron
sudo mkdir -p /etc/hmap /var/backups/hmap
sudo chown user1:user1 /etc/hmap /var/backups/hmap
chmod 700 /etc/hmap /var/backups/hmap
openssl rand -base64 48 > /etc/hmap/backup.key
chmod 600 /etc/hmap/backup.key

# 3. Scratch database for test restores; the backup user needs full rights on it
mysql -u root -p -e "CREATE DATABASE hmap_db_restore_test CHARACTER SET utf8mb4;
  GRANT ALL ON hmap_db_restore_test.* TO 'hris'@'localhost';"
#    The account in ml/.env also needs SELECT, LOCK TABLES, SHOW VIEW, TRIGGER
#    and EVENT on hmap_db for mysqldump.

# 4. Add the BACKUP_* lines from ml/.env.example to ml/.env, then try it
ml/.venv/bin/python ml/backup_db.py create
ml/.venv/bin/python ml/backup_db.py verify
```

### Keep a copy of the key off the server

**Without the key, the backups cannot be decrypted.** Not by the
developer, not by anyone. Right after generating it:

1. Print `/etc/hmap/backup.key` (or write it down). Seal it in an envelope
   marked "H-MAP backup key" and give it to the CESU head for the CHO safe.
2. Do not store the key next to the backup files, in the repository, or in email.
3. Seal a copy of `laravel/.env` with it. Its `APP_KEY` decrypts the staff
   authenticator secrets in `user_mfa`, so a restored database needs the same key.
4. If the key is ever exposed, generate a new one, run `create` straight away,
   and keep the old key only until every backup made with it has aged out.

---

## Schedule (cron)

`crontab -e` as `user1`:

```cron
# H-MAP: nightly encrypted backup 02:00; test restore Sundays 03:00
0 2 * * *  cd /var/www/html/hmap && ml/.venv/bin/python ml/backup_db.py create >> /var/log/hmap/backup.log 2>&1
0 3 * * 0  cd /var/www/html/hmap && ml/.venv/bin/python ml/backup_db.py verify >> /var/log/hmap/backup.log 2>&1
```

(`sudo mkdir -p /var/log/hmap && sudo chown user1 /var/log/hmap` first.)

The Reports panel shows the last backup in red if it is more than 36 hours
old, and the last test restore in red if it failed. Check it at least weekly.

### Off-site copy

A backup on the same disk does not survive a disk failure. At least weekly,
copy the newest `.enc` file somewhere else. Two options:

- **another CHO/LGU server**: `rsync -a /var/backups/hmap/ backup@<host>:/srv/hmap-backups/`
- **an encrypted USB drive** kept in the CESU office

The files are already encrypted, so a copy is safe without the key.

---

## Commands

```bash
python ml/backup_db.py list                         # last 20 backups and verify results
python ml/backup_db.py verify                       # test-restore the newest backup
python ml/backup_db.py verify --id 12               # test-restore a specific one
python ml/backup_db.py restore --id 12 --target hmap_db_recovered
```

`verify` exits non-zero on failure. The causes it reports:

| Message | Meaning |
|---|---|
| `checksum mismatch` | The file changed after it was written (disk fault, tampering). Use an earlier backup. |
| `could not decrypt … wrong key` | `BACKUP_KEY_FILE` is not the key this backup was made with. |
| `<table>: expected N, restored M` | The dump is incomplete. Check `/var/log/hmap/backup.log` for that night. |
| `backup file missing` | The file was pruned or moved. |

---

## Recovering production

1. **Restore into a new database first** and look at it before touching production:
   ```bash
   mysql -u root -p -e "CREATE DATABASE hmap_db_recovered CHARACTER SET utf8mb4;
     GRANT ALL ON hmap_db_recovered.* TO 'hris'@'localhost';"
   python ml/backup_db.py list
   python ml/backup_db.py restore --id <N> --target hmap_db_recovered
   ```
2. Confirm the newest case dates and counts look right in `hmap_db_recovered`.
3. Stop writes: put Laravel in maintenance mode (`php artisan down`) and stop `hmap-ml`.
4. Restore over production (the tool refuses this without the flag):
   ```bash
   python ml/backup_db.py restore --id <N> --target hmap_db --overwrite-live
   ```
5. `php artisan up`, start `hmap-ml`, and run the smoke test in `docs/DEPLOYMENT.md`.
6. Record the incident in the audit log notes. Cases encoded after the backup
   time must be re-encoded from the DRU reports.

### By hand, without the script

If Python is unavailable, standard tools are enough:

```bash
openssl enc -d -aes-256-cbc -pbkdf2 -iter 200000 -salt \
    -pass file:/etc/hmap/backup.key -in hmap_db_YYYYMMDD_HHMMSS.sql.gz.enc \
  | gunzip | mysql -u root -p --default-character-set=utf8mb4 hmap_db_recovered
```

Check the SHA-256 first (`sha256sum <file>`) against `backup_log.sha256`.

---

## Tested

The tests were run on 2026-10-22 against a throwaway MariaDB 10.4 loaded
with `ml/schema.sql`. All of the following worked:

- create, then verify (14 tables matched)
- restoring into a separate database, with UTF-8 ("Parañaque") preserved
- refusing to overwrite the live database without the flag
- detecting a file with one flipped byte (checksum mismatch)
- refusing a wrong key
- detecting a row-count mismatch
- a manual decrypt with `openssl` alone
- pruning, which never deletes the backup just made, even at 0-day retention
