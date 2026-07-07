#!/usr/bin/env python3
"""Database setup script for RAMon Chatbot.

This script initializes the PostgreSQL database tables required by the
LangGraph ShallowPostgresSaver checkpointer.

Init the products table with embeddings

Run this script once before
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
import psycopg

load_dotenv()
database_url = os.getenv("DATABASE_URL")
if not database_url:
    print("Error: DATABASE_URL environment variable is required", file=sys.stderr)
    sys.exit(1)

def setup_checkpointer():    
    try:
        with ShallowPostgresSaver.from_conn_string(database_url) as checkpointer:
            checkpointer.setup()
        print("Database checkpointer setup completed successfully.")
    except Exception as exc:
        print(f"Error setting up database: {exc}", file=sys.stderr)
        sys.exit(1)

    
def setup_products_table():
    with psycopg.connect(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute("CREATE EXTENSION IF NOT EXISTS vector")
            cur.execute("""
                CREATE TABLE IF NOT EXISTS products (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT DEFAULT '',
                    price DOUBLE PRECISION DEFAULT 0.0,
                    url TEXT DEFAULT '',
                    stock INTEGER DEFAULT 0,
                    embedding VECTOR(1536)
                )
            """)
        print("Database products table initialized successfully.")

if __name__ == "__main__":
    setup_checkpointer()
    setup_products_table()
