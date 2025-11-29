#!/usr/bin/env bash
set -euo pipefail
IFS=$'\n\t'

log() { printf '%s %s\n' "[entrypoint]" "$*"; }

log "Starting entrypoint…"

# ── Ждём БД ────────────────────────────────────────────────────────────────────
log "Waiting for the database to be ready (up to 60s)…"

python - <<'PY'
import os, time, psycopg2
from urllib.parse import urlparse

db_url = os.environ.get("DATABASE_URL")
if db_url:
    url = urlparse(db_url)
    cfg = dict(
        dbname=(url.path[1:] or os.environ.get("POSTGRES_DB","postgres")),
        user=(url.username or os.environ.get("POSTGRES_USER","postgres")),
        password=(url.password or os.environ.get("POSTGRES_PASSWORD","")),
        host=(url.hostname or "db"),
        port=(url.port or 5432),
    )
else:
    cfg = dict(
        dbname=os.environ.get("POSTGRES_DB","postgres"),
        user=os.environ.get("POSTGRES_USER","postgres"),
        password=os.environ.get("POSTGRES_PASSWORD",""),
        host=os.environ.get("DB_HOST","db"),
        port=int(os.environ.get("DB_PORT","5432")),
    )

deadline = time.time() + 60
attempt = 1
while True:
    try:
        conn = psycopg2.connect(connect_timeout=2, **cfg)
        conn.close()
        print("[entrypoint] DB is ready.")
        break
    except Exception as e:
        if time.time() > deadline:
            print("[entrypoint] DB is not ready after 60s:", repr(e))
            raise SystemExit(1)
        print(f"[entrypoint] DB not ready (try {attempt}):", repr(e))
        attempt += 1
        time.sleep(1)
PY

# ── Миграции ───────────────────────────────────────────────────────────────────
log "Applying migrations…"
python manage.py migrate --noinput

# ── Статика ────────────────────────────────────────────────────────────────────
log "Collecting static files…"
mkdir -p /app/collected_static
python manage.py collectstatic --noinput

# ── Локали (не критично) ───────────────────────────────────────────────────────
log "Compiling translations (best effort)…"
python - <<'PY' || true
import subprocess
try:
    subprocess.check_call(["python", "manage.py", "compilemessages"])
except Exception as e:
    print("[entrypoint] compilemessages skipped/failed:", repr(e))
PY

log "Startup done. Launching app: $*"
exec "$@"