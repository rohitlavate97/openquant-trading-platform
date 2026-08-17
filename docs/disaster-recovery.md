# OpenQuant Disaster Recovery & Backup Runbook

This document outlines procedures for data protection, automated backups, and disaster recovery.

---

## 1. Automated PostgreSQL Backup Schedule

### Backup Script (`/opt/openquant/scripts/backup-db.sh`)
```bash
#!/bin/bash
set -eo pipefail

BACKUP_DIR="/var/backups/openquant"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
FILENAME="$BACKUP_DIR/openquant_db_$TIMESTAMP.sql.gz"

mkdir -p "$BACKUP_DIR"

# Execute pg_dump from Docker container
docker compose -f /opt/openquant/docker-compose.prod.yml exec -T postgres \
  pg_dump -U openquant_user -d openquant | gzip > "$FILENAME"

# Retain backups for 30 days
find "$BACKUP_DIR" -type f -name "openquant_db_*.sql.gz" -mtime +30 -delete

echo "[$(date)] Backup completed: $FILENAME"
```

### Configure Daily Cron Schedule
```bash
# Add to root crontab
crontab -e
# Run daily at 01:00 UTC
0 1 * * * /opt/openquant/scripts/backup-db.sh >> /var/log/openquant-backup.log 2>&1
```

---

## 2. Database Restoration Drill

### Step 1: Stop Application Containers
```bash
docker compose -f docker-compose.prod.yml stop backend frontend
```

### Step 2: Restore from Gzipped SQL Dump
```bash
gunzip -c /var/backups/openquant/openquant_db_YYYYMMDD_HHMMSS.sql.gz | \
  docker compose -f docker-compose.prod.yml exec -T postgres \
  psql -U openquant_user -d openquant
```

### Step 3: Run Database Migrations (if necessary)
```bash
docker compose -f docker-compose.prod.yml run --rm backend uv run alembic upgrade head
```

### Step 4: Restart Application
```bash
docker compose -f docker-compose.prod.yml start backend frontend
```

---

## 3. Cryptographic Master Secret Recovery

If recovering onto a new server:
1. Ensure the exact same `OPENQUANT_MASTER_SECRET` is placed in `.env.production`.
2. Verify secrets vault integrity by executing:
```bash
docker compose -f docker-compose.prod.yml exec backend \
  uv run pytest -v tests/integration/test_secrets_api.py
```
If the master secret matches, all broker API keys and OAuth tokens will decrypt without errors.
