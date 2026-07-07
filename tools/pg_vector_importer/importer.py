import csv
import os
import sys

from dotenv import load_dotenv
from openai import OpenAI
from pgvector.psycopg2 import register_vector
from sqlalchemy import create_engine, text

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
CSV_FILE = os.path.join(os.path.dirname(__file__), "products.csv")
EMBEDDING_MODEL = "text-embedding-3-small"
BATCH_SIZE = 50


def get_embeddings(client: OpenAI, texts: list[str]) -> list[list[float]]:
    resp = client.embeddings.create(input=texts, model=EMBEDDING_MODEL)
    return [item.embedding for item in resp.data]


def upload_products():
    if not OPENAI_API_KEY:
        print("Error: OPENAI_API_KEY is not set")
        sys.exit(1)

    openai_client = OpenAI(api_key=OPENAI_API_KEY)

    with open(CSV_FILE, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        products = list(reader)

    print(f"Loaded {len(products)} products from {CSV_FILE}")

    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        register_vector(conn.connection.driver_connection)

        batch = []
        for i, row in enumerate(products):
            text_for_embedding = (
                f"name: {row['name']}\ndescription: {row['description']}"
            )
            batch.append((
                row["sku"],
                row["name"],
                row["description"],
                float(row["price"]) if row.get("price") else 0.0,
                row.get("url", ""),
                int(row["stock"]) if row.get("stock") else 0,
                text_for_embedding,
            ))

            if len(batch) >= BATCH_SIZE or i == len(products) - 1:
                texts = [b[6] for b in batch]
                print(
                    f"Embedding batch of {len(batch)} products "
                    f"({i + 1 - len(batch) + 1}–{i + 1})..."
                )
                embeddings = get_embeddings(openai_client, texts)

                for (pid, name, desc, price, url, stock, _), emb in zip(batch, embeddings):
                    conn.execute(
                        text("""
                            INSERT INTO products
                                (id, name, description, price, url, stock, embedding)
                            VALUES
                                (:id, :name, :desc, :price, :url, :stock, :embedding)
                            ON CONFLICT (id) DO UPDATE SET
                                name = EXCLUDED.name,
                                description = EXCLUDED.description,
                                price = EXCLUDED.price,
                                url = EXCLUDED.url,
                                stock = EXCLUDED.stock,
                                embedding = EXCLUDED.embedding
                        """),
                        {
                            "id": pid,
                            "name": name,
                            "desc": desc,
                            "price": price,
                            "url": url,
                            "stock": stock,
                            "embedding": emb,
                        },
                    )
                conn.commit()
                batch = []

    print(f"Upload complete. {len(products)} products inserted.")


if __name__ == "__main__":
    upload_products()
