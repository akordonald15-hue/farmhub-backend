#!/usr/bin/env bash
set -e

python - <<'PY'
import os
import time
import psycopg2

db_url = os.environ.get("DATABASE_URL")
if not db_url:
    raise SystemExit("DATABASE_URL is not set")

for _ in range(30):
    try:
        conn = psycopg2.connect(db_url)
        conn.close()
        break
    except Exception:
        time.sleep(2)
else:
    raise SystemExit("Database is not ready")
PY

python manage.py migrate --noinput
python manage.py collectstatic --noinput

exec gunicorn backend.wsgi:application \
  --bind 0.0.0.0:8000 \
  --workers 3 \
  --timeout 60
