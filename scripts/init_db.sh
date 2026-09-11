#!/bin/bash
# Database initialization script
# This script runs the database schema and migrations

set -e

echo "Initializing database..."

# Wait for PostgreSQL to be ready
until pg_isready -h "${DB_HOST:-localhost}" -p "${DB_PORT:-5432}" -U "${DB_USER:-postgres}"; do
    echo "Waiting for PostgreSQL to be ready..."
    sleep 2
done

# Run database schema
if [ -f "database.sql" ]; then
    echo "Running database.sql..."
    PGPASSWORD="${DB_PASSWORD:-postgres}" psql -h "${DB_HOST:-localhost}" -p "${DB_PORT:-5432}" -U "${DB_USER:-postgres}" -d "${DB_NAME:-vectordb}" -f database.sql
fi

# Run migrations in order
if [ -d "migrations" ]; then
    echo "Running migrations..."
    for migration in migrations/*.sql; do
        if [ -f "$migration" ]; then
            echo "Running migration: $migration"
            PGPASSWORD="${DB_PASSWORD:-postgres}" psql -h "${DB_HOST:-localhost}" -p "${DB_PORT:-5432}" -U "${DB_USER:-postgres}" -d "${DB_NAME:-vectordb}" -f "$migration"
        fi
    done
fi

echo "Database initialization complete!"

