#!/bin/bash
set -e

# Build DATABASE_URL from individual components
# This allows using the same .env file locally and in Docker (with DB_HOST override)
export DATABASE_URL="postgresql://${DB_USER}:${DB_PASSWORD}@${DB_HOST}:${DB_PORT}/${DB_NAME}"

# yoyo-migrations requires postgresql+psycopg:// scheme
export YOYO_DATABASE_URL="postgresql+psycopg://${DB_USER}:${DB_PASSWORD}@${DB_HOST}:${DB_PORT}/${DB_NAME}"

echo "Waiting for PostgreSQL to be ready..."
until python -c "import psycopg; psycopg.connect('$DATABASE_URL')" 2>/dev/null; do
    echo "PostgreSQL is unavailable - sleeping"
    sleep 2
done
echo "PostgreSQL is ready!"

echo "Running database migrations..."
yoyo apply --database "$YOYO_DATABASE_URL" --batch

# Start cron daemon for the sync worker
if command -v crond &> /dev/null; then
    echo "Starting cron daemon for sync worker..."
    crond
elif command -v cron &> /dev/null; then
    echo "Starting cron daemon for sync worker..."
    cron
fi

echo "Starting FastAPI server..."
exec "$@"
