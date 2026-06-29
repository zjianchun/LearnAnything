#!/bin/sh
# Auto-seed database if it doesn't exist
DB_PATH="/app/db/learn.db"
if [ ! -f "$DB_PATH" ]; then
    echo "🌱 First run: seeding database..."
    python /app/seed.py
fi
exec uvicorn main:app --host 0.0.0.0 --port 8000
