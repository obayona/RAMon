#!/usr/bin/env python3
"""Product importer for RAMon database.

Imports products from CSV, generates embeddings via OpenAI, and stores
them in PostgreSQL with pgvector.

Usage:
    python importer.py                    # Import from products.csv
    python importer.py --csv data.csv     # Import from custom CSV
    python importer.py --export out.csv   # Export products with embeddings

Environment Variables:
    DATABASE_URL: PostgreSQL connection string (required)
    OPENAI_API_KEY: OpenAI API key (required for import, not for export)
"""
import argparse
import csv
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI
from pgvector.psycopg2 import register_vector
from sqlalchemy import create_engine, text

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DEFAULT_CSV = Path(__file__).parent / "wc-products.csv"
EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIMENSIONS = 1536
BATCH_SIZE = 50


def get_embeddings(client: OpenAI, texts: list[str]) -> list[list[float]]:
    """Generate embeddings for a batch of texts."""
    resp = client.embeddings.create(input=texts, model=EMBEDDING_MODEL)
    return [item.embedding for item in resp.data]


def import_products(csv_file: Path) -> None:
    """Import products from CSV with embedding generation."""
    if not DATABASE_URL:
        print("Error: DATABASE_URL is not set", file=sys.stderr)
        sys.exit(1)
    if not OPENAI_API_KEY:
        print("Error: OPENAI_API_KEY is not set", file=sys.stderr)
        sys.exit(1)

    openai_client = OpenAI(api_key=OPENAI_API_KEY)

    with open(csv_file, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        products = list(reader)

    print(f"Loaded {len(products)} products from {csv_file}")

    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        register_vector(conn.connection.driver_connection)

        batch = []
        for i, row in enumerate(products):
            
            product = {
                "product_id": row.get("ID"),
                "sku": row.get("SKU", ""),
                "name": row["Name"],
                "description": row.get("Description", ""),
                "stock": int(row["Stock"]) if row.get("stock") else 0,
                "price": float(row["Sale price"]) if row.get("Sale price") else 0.0,
                "categories": row.get("Categories", "")
            }
            text_for_embedding = f"name: {product['name']}\ndescription: {product['description']}\ncategories: {product['categories']}"
            product['text_for_embedding'] = text_for_embedding
            batch.append(product)

            if len(batch) >= BATCH_SIZE or i == len(products) - 1:
                texts = [b["text_for_embedding"] for b in batch]
                print(
                    f"Embedding batch of {len(batch)} products "
                    f"({i + 1 - len(batch) + 1}–{i + 1})..."
                )
                embeddings = get_embeddings(openai_client, texts)

                for product, emb in zip(batch, embeddings):
                    conn.execute(
                        text("""
                            INSERT INTO products
                                (product_id, sku, name, description, stock, price, categories, embedding)
                            VALUES
                                (:product_id, :sku, :name, :description, :stock, :price, :categories, :embedding)
                            ON CONFLICT (id) DO NOTHING
                        """),
                        {
                            "product_id": product["product_id"],
                            "sku": product["sku"],
                            "name": product["name"],
                            "description": product["description"],
                            "stock": product["stock"],
                            "price": product["price"],
                            "categories": product["categories"],
                            "embedding": emb,
                        },
                    )
                conn.commit()
                batch = []

    print(f"Import complete. {len(products)} products processed.")


def export_products(output_file: Path) -> None:
    """Export products with embeddings to CSV."""
    if not DATABASE_URL:
        print("Error: DATABASE_URL is not set", file=sys.stderr)
        sys.exit(1)

    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT product_id, sku, name, description, categories, price, stock, embedding::text
            FROM products
        """))
        rows = result.fetchall()

    if not rows:
        print("No products found in database.")
        return

    fieldnames = ["product_id", "sku", "name", "description", "categories", "price", "stock", "embedding"]
    
    with open(output_file, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for row in rows:
            writer.writerow({
                "product_id": row[0],
                "sku": row[1] or "",
                "name": row[2],
                "description": row[3] or "",
                "categories": row[4] or "",
                "price": row[5],
                "stock": row[6],
                "embedding": row[7],
            })

    print(f"Exported {len(rows)} products to {output_file}")


def import_from_fixtures(csv_file: Path) -> None:
    """Import products from fixtures CSV (with pre-computed embeddings)."""
    if not DATABASE_URL:
        print("Error: DATABASE_URL is not set", file=sys.stderr)
        sys.exit(1)

    with open(csv_file, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        products = list(reader)

    print(f"Loaded {len(products)} products from fixtures {csv_file}")

    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        register_vector(conn.connection.driver_connection)

        for i, row in enumerate(products):
            # Parse embedding from text format [0.1,0.2,...] to list
            embedding_text = row.get("embedding", "")
            if embedding_text:
                # Remove brackets and split
                embedding = [float(x) for x in embedding_text.strip("[]").split(",")]
            else:
                embedding = None

            conn.execute(
                text("""
                    INSERT INTO products
                        (product_id, sku, name, description, stock, price, categories, embedding)
                    VALUES
                        (:product_id, :sku, :name, :description, :stock, :price, :categories, :embedding)
                    ON CONFLICT (id) DO NOTHING
                """),
                {
                    "product_id": row["product_id"],
                    "sku": row["sku"],
                    "name": row["name"],
                    "description": row["description"],
                    "stock": int(row["stock"]),
                    "price": float(row["price"]),
                    "categories": row["categories"],
                    "embedding": embedding,
                },
            )
            
            if (i + 1) % 100 == 0:
                print(f"Imported {i + 1}/{len(products)} products...")
                conn.commit()
        
        conn.commit()

    print(f"Import complete. {len(products)} products loaded from fixtures.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Product importer/exporter for RAMon")
    parser.add_argument(
        "--csv",
        type=Path,
        default=DEFAULT_CSV,
        help="CSV file to import (default: products.csv)"
    )
    parser.add_argument(
        "--export",
        type=Path,
        metavar="OUTPUT",
        help="Export products with embeddings to CSV"
    )
    parser.add_argument(
        "--fixtures",
        type=Path,
        metavar="FILE",
        help="Import from fixtures CSV (with pre-computed embeddings)"
    )
    args = parser.parse_args()

    if args.export:
        export_products(args.export)
    elif args.fixtures:
        import_from_fixtures(args.fixtures)
    else:
        import_products(args.csv)


if __name__ == "__main__":
    main()
