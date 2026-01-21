#!/bin/bash

set -e

echo "🛠️ Applying database migrations..."
export FLASK_APP=tab_view
flask db upgrade

echo "🚀 Starting application..."
exec gunicorn "tab_view:create_app()" \
    --bind 0.0.0.0:8000 \
    --workers 3 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile -
