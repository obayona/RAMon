#!/bin/bash
set -e

# Convert DATABASE_URL to yoyo format (postgresql+psycopg://)
YOYO_DATABASE_URL="${DATABASE_URL/postgresql:\/\//postgresql+psycopg:\/\/}"

echo "Waiting for PostgreSQL to be ready..."
until python -c "import psycopg; psycopg.connect('$DATABASE_URL')" 2>/dev/null; do
    echo "PostgreSQL is unavailable - sleeping"
    sleep 2
done
echo "PostgreSQL is ready!"

echo "Running database migrations..."
yoyo apply --database "$YOYO_DATABASE_URL" --batch

echo "Starting FastAPI server..."
exec "$@"
