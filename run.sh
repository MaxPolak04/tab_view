#!/bin/bash

set -e

export PYTHONPATH=/app
export FLASK_APP=tab_view

# 1. Apply database migrations
echo "🛠️ Applying database migrations..."
flask db upgrade

# 2. Seed initial data
echo "🌱 Seeding initial data..."
uv run python -m tab_view.seed
# uv run python tab_view/seed.py

# 3. Start the application server
echo "🚀 Starting application..."
exec gunicorn "tab_view:create_app()" \
    --bind 0.0.0.0:8000 \
    --workers 3 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile -
