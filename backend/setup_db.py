#!/usr/bin/env python3
"""Database setup script for RAMon Chatbot.

This script initializes the PostgreSQL database tables required by the
LangGraph ShallowPostgresSaver checkpointer. Run this script once before
starting the server for the first time, or after database migrations.

Usage:
    python setup_db.py

Environment Variables:
    DATABASE_URL: PostgreSQL connection string (required)
"""
import os
import sys

from dotenv import load_dotenv
from langgraph.checkpoint.postgres import ShallowPostgresSaver


def main():
    load_dotenv()
    
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("Error: DATABASE_URL environment variable is required", file=sys.stderr)
        sys.exit(1)
    
    print(f"Setting up database tables...")
    print(f"Connecting to: {database_url.split('@')[-1] if '@' in database_url else 'database'}")
    
    try:
        with ShallowPostgresSaver.from_conn_string(database_url) as checkpointer:
            checkpointer.setup()
        print("Database setup completed successfully.")
    except Exception as exc:
        print(f"Error setting up database: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
