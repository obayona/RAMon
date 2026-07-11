#!/usr/bin/env python3
"""Product table dump for RAMon database.

dump products from database.

Usage:
    python dump.py                             # dump products table
    python dump.py --output fixture.pkl.gz     # dump with output option

Environment Variables:
    DATABASE_URL: PostgreSQL connection string (required)
"""
import argparse
import os
import gzip
import pickle
from pathlib import Path
import psycopg
from pgvector.psycopg import register_vector
from dotenv import load_dotenv

load_dotenv()

# --- Configuration ---
DB_URL = os.getenv("DATABASE_URL")
OUTPUT_FILE = "fixture.pkl.gz"
ROW_LIMIT = 100

def dump_pgvector_table(output):    
    try:
        # Connect to PostgreSQL
        with psycopg.connect(DB_URL) as conn:
            register_vector(conn)
            
            with conn.cursor() as cur:
                
                # Execute the query with the limit
                query = f"SELECT * FROM products LIMIT {ROW_LIMIT};"
                cur.execute(query)
                
                # Extract column names for context
                column_names = [desc[0] for desc in cur.description]
                
                # Fetch the data
                rows = cur.fetchall()
                
        # Structure the payload
        payload = {
            "columns": column_names,
            "data": rows
        }
        
        # Write to a GZIP compressed Pickle (Binary) file
        print(f"Compressing and writing to {output}...")
        with gzip.open(output, 'wb') as f:
            pickle.dump(payload, f, protocol=pickle.HIGHEST_PROTOCOL)
            
        print(f"Success! Dumped {len(rows)} rows to {output}.")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Product dump for RAMon")
    parser.add_argument(
        "--output",
        type=Path,
        default=OUTPUT_FILE,
        help="Output file for dump"
    )

    args = parser.parse_args()
    dump_pgvector_table(args.output)
