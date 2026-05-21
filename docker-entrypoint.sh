#!/bin/bash

set -e

echo "🔄 Initializing Automation App..."

cd /app

if [ ! -f "automation.db" ]; then
    echo "📦 Creating database..."
    python -c "from app.core.database import init_db; init_db()"
    echo "👤 Creating default admin user (admin/admin123)..."
    python -c "from app.core.database import get_db_context; from app.services.auth import create_default_admin; db = next(get_db_context()); create_default_admin(db)"
fi

echo "✅ Initialization complete!"
echo ""
echo "📋 Default credentials:"
echo "   Username: admin"
echo "   Password: admin123"
echo ""
echo "🌐 Starting server on port ${APP_PORT:-8000}..."
exec python cli.py web --host 0.0.0.0 --port ${APP_PORT:-8000}