#!/usr/bin/env python3
"""Restore Product table dump for RAMon database.

restore dump products from database.

Usage: 
    python load_fixture.py --input fixture.pkl.gz     # restore products table

Environment Variables:
    DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD: Individual DB settings
    DATABASE_URL: PostgreSQL connection string (alternative to individual settings)
"""
import os
import argparse
import gzip
import pickle
import psycopg
from pgvector.psycopg import register_vector
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


def _get_database_url() -> str:
    """Build DATABASE_URL from individual components or use existing value."""
    existing_url = os.environ.get("DATABASE_URL", "").strip()
    if existing_url:
        return existing_url
    
    return (
        f"postgresql://{os.environ['DB_USER']}:{os.environ['DB_PASSWORD']}"
        f"@{os.environ['DB_HOST']}:{os.environ['DB_PORT']}/{os.environ['DB_NAME']}"
    )


# --- Configuration ---
DB_URL = _get_database_url()
INPUT_FILE = "fixture.pkl.gz"

def restore_pgvector_table(input_file):
    print(f"Reading data from {input_file}...")
    
    try:
        # 1. Load the compressed binary data back into memory
        with gzip.open(input_file, 'rb') as f:
            payload = pickle.load(f)
            
        columns = payload["columns"]
        data = payload["data"]
        
        if not data:
            print("No data found in the dump file.")
            return

        print(f"Loaded {len(data)} rows.")

        # 2. Connect to PostgreSQL and insert
        with psycopg.connect(DB_URL) as conn:
            register_vector(conn)
            
            with conn.cursor() as cur:
                # Dynamically construct the INSERT query based on the payload's columns
                col_names_str = ", ".join(columns)
                placeholders = ", ".join(["%s"] * len(columns))
                
                query = f"INSERT INTO products ({col_names_str}) VALUES ({placeholders})"
                
                print(f"Inserting data into 'products'...")
                
                # executemany automatically handles batching and escaping the data
                cur.executemany(query, data)
                
            # Don't forget to commit the transaction!
            conn.commit()
            print("Success! Data upload complete.")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Product dump for RAMon")
    parser.add_argument(
        "--input",
        type=Path,
        default=INPUT_FILE,
        help="Input file for restore"
    )

    args = parser.parse_args()
    restore_pgvector_table(args.input)
