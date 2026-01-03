#!/bin/bash
# ============================================
# Database Initialization Script
# ============================================

set -e

echo "🔧 Running migrations..."

# Run migrations in order
for file in /docker-entrypoint-initdb.d/migrations/*.sql; do
    if [ -f "$file" ]; then
        echo "  → Running $(basename $file)..."
        psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" -f "$file"
    fi
done

echo "🌱 Running seeds..."

# Run seeds
for file in /docker-entrypoint-initdb.d/seeds/*.sql; do
    if [ -f "$file" ]; then
        echo "  → Seeding $(basename $file)..."
        psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" -f "$file"
    fi
done

echo "✅ Database initialization complete!"
