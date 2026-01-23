#!/bin/bash

set -e

echo "📦 Syncing dependencies..."
uv sync --locked

echo "🛠️ Applying database migrations..."
export FLASK_APP=tab_view
uv run flask db upgrade

echo "🚀 Starting application..."
exec uv run gunicorn "tab_view:create_app()" \
    --bind 0.0.0.0:8000 \
    --workers 3 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile -
