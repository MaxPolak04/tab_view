#!/bin/bash


echo "📦 Applying database migrations..."
export FLASK_APP=tab_view


echo "🛠️ Running flask db upgrade..."
flask db upgrade
echo "✅ Migrations applied successfully."


echo "🏃‍♂️ Starting app..."
gunicorn "tab_view:create_app()" \
    --bind 0.0.0.0:8000 \
    --workers 3 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile -

