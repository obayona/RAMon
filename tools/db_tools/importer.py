#!/usr/bin/env python3
"""Product importer for RAMon database.

Imports products from CSV, generates embeddings via OpenAI, and stores
them in PostgreSQL with pgvector.

Usage:
    python importer.py                    # Import from products.csv
    python importer.py --csv data.csv     # Import from custom CSV

Environment Variables:
    DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD: Individual DB settings
    DATABASE_URL: PostgreSQL connection string (alternative to individual settings)
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


def _get_database_url() -> str:
    """Build DATABASE_URL from individual components or use existing value."""
    return (
        f"postgresql://{os.environ['DB_USER']}:{os.environ['DB_PASSWORD']}"
        f"@{os.environ['DB_HOST']}:{os.environ['DB_PORT']}/{os.environ['DB_NAME']}"
    )


DATABASE_URL = _get_database_url()
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
            price = row["Regular price"]
            price = float(price.replace(",", "."))
            product = {
                "product_id": row.get("ID"),
                "sku": row.get("SKU", ""),
                "name": row["Name"],
                "description": row.get("Description", ""),
                "stock": int(row["Stock"]) if len(row["Stock"]) else 0,
                "price": price,
                "categories": row.get("Categories", ""),
                "image_url": (row.get("Images", ",").split())[0].strip(),
                "status": "published",
                "in_stok": True,
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

def main() -> None:
    parser = argparse.ArgumentParser(description="Product csv importer for RAMon")
    parser.add_argument(
        "--csv",
        type=Path,
        default=DEFAULT_CSV,
        help="CSV file to import (default: products.csv)"
    )

    args = parser.parse_args()

    import_products(args.csv)


if __name__ == "__main__":
    main()
