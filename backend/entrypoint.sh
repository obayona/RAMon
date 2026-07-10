#!/bin/bash
set -e

echo "Waiting for PostgreSQL to be ready..."
until python -c "import psycopg; psycopg.connect('$DATABASE_URL')" 2>/dev/null; do
    echo "PostgreSQL is unavailable - sleeping"
    sleep 2
done
echo "PostgreSQL is ready!"

echo "Running database setup..."
python setup_db.py

echo "Starting FastAPI server..."
exec "$@"
