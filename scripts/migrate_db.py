#!/usr/bin/env python3
"""
Database migration script.
Runs SQL migration files in order.
"""
import os
import sys
import psycopg2
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


def run_migration_file(conn, file_path):
    """Run a single migration file"""
    print(f"Running migration: {file_path.name}")
    
    with open(file_path, 'r') as f:
        sql = f.read()
    
    try:
        with conn.cursor() as cur:
            cur.execute(sql)
        conn.commit()
        print(f"  ✓ Success")
        return True
    except Exception as e:
        conn.rollback()
        print(f"  ✗ Error: {e}")
        return False


def main():
    """Run all migrations in order"""
    # Get database URL from environment
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("Error: DATABASE_URL environment variable not set")
        sys.exit(1)
    
    # Connect to database
    try:
        conn = psycopg2.connect(database_url)
        print(f"Connected to database")
    except Exception as e:
        print(f"Error connecting to database: {e}")
        sys.exit(1)
    
    # Get migrations directory
    migrations_dir = Path(__file__).parent.parent / "migrations"
    if not migrations_dir.exists():
        print(f"Error: Migrations directory not found: {migrations_dir}")
        sys.exit(1)
    
    # Get all SQL files and sort them
    migration_files = sorted(migrations_dir.glob("*.sql"))
    
    if not migration_files:
        print("No migration files found")
        sys.exit(0)
    
    print(f"Found {len(migration_files)} migration file(s)")
    print("-" * 60)
    
    # Run migrations
    success_count = 0
    for migration_file in migration_files:
        if run_migration_file(conn, migration_file):
            success_count += 1
        else:
            print(f"\nMigration failed. Stopping.")
            break
        print()
    
    conn.close()
    
    print("-" * 60)
    print(f"Completed: {success_count}/{len(migration_files)} migrations successful")
    
    if success_count == len(migration_files):
        print("All migrations completed successfully!")
        sys.exit(0)
    else:
        print("Some migrations failed.")
        sys.exit(1)


if __name__ == "__main__":
    main()

