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

# Import Vector class so pickle can deserialize pgvector objects
from pgvector.psycopg import Vector

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


class PickleUnpickler(pickle.Unpickler):
    """Custom unpickler to handle pgvector module renames."""
    
    def find_class(self, module, name):
        # Redirect old pgvector.vector module to pgvector.psycopg
        if module == "pgvector.vector" and name == "Vector":
            return Vector
        return super().find_class(module, name)


def restore_pgvector_table(input_file):
    print(f"Reading data from {input_file}...")
    
    try:
        # 1. Load the compressed binary data back into memory
        # Use custom unpickler to handle pgvector module path changes
        with gzip.open(input_file, 'rb') as f:
            payload = PickleUnpickler(f).load()
            
        columns = payload["columns"]
        data = payload["data"]
        
        if not data:
            print("No data found in the dump file.")
            return

        print(f"Loaded {len(data)} rows with columns: {columns}")

        # 2. Connect to PostgreSQL and insert
        with psycopg.connect(DB_URL) as conn:
            register_vector(conn)
            
            with conn.cursor() as cur:
                # Get actual table columns from database
                cur.execute("""
                    SELECT column_name FROM information_schema.columns 
                    WHERE table_name = 'products' 
                    ORDER BY ordinal_position
                """)
                db_columns = {row[0] for row in cur.fetchall()}
                
                # Filter to only columns that exist in both fixture and database
                # Skip 'id' column as it's auto-generated
                valid_indices = []
                valid_columns = []
                for i, col in enumerate(columns):
                    if col in db_columns and col != 'id':
                        valid_indices.append(i)
                        valid_columns.append(col)
                
                skipped = set(columns) - set(valid_columns) - {'id'}
                if skipped:
                    print(f"Skipping columns not in schema: {skipped}")
                
                # Filter data to only include valid columns
                filtered_data = [
                    tuple(row[i] for i in valid_indices)
                    for row in data
                ]
                
                col_names_str = ", ".join(valid_columns)
                placeholders = ", ".join(["%s"] * len(valid_columns))
                
                query = f"INSERT INTO products ({col_names_str}) VALUES ({placeholders})"
                
                print(f"Inserting data into 'products' ({len(valid_columns)} columns)...")
                
                # executemany automatically handles batching and escaping the data
                cur.executemany(query, filtered_data)
                
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
