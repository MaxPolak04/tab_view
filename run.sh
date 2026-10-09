#!/bin/bash
set -e

export PYTHONPATH=/app
export FLASK_APP=tab_view

# 1. Wait for MySQL database readiness
echo "⏳ Waiting for database connection..."
python - <<'EOF'
import os
import sys
import time
from sqlalchemy import create_engine, text

db_url = os.getenv("DATABASE_URL")
if not db_url:
    print("❌ Error: DATABASE_URL environment variable is not set.")
    sys.exit(1)

max_retries = 30
retry_interval = 2

for attempt in range(1, max_retries + 1):
    try:
        engine = create_engine(db_url, connect_args={"connect_timeout": 3})
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("   ✅ Database is reachable and ready to accept queries.")
        sys.exit(0)
    except Exception as exc:
        print(f"   ⏳ Attempt {attempt}/{max_retries}: Database not ready ({exc}). Retrying in {retry_interval}s...")
        time.sleep(retry_interval)

print("❌ Error: Timed out waiting for database connection.")
sys.exit(1)
EOF

# 2. Apply database migrations
echo "🛠️ Applying database migrations..."
flask db upgrade

# 3. Seed initial data
echo "🌱 Seeding initial data..."
python -m tab_view.seed

# 4. Start the application server
echo "🚀 Starting application..."
if [ "$#" -gt 0 ]; then
    exec "$@"
else
    exec gunicorn "tab_view:create_app()" \
        --bind 0.0.0.0:8000 \
        --workers 2 \
        --threads 4 \
        --timeout 120 \
        --access-logfile - \
        --error-logfile -
fi
