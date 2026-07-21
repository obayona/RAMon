#!/usr/bin/env python3
"""Background worker that processes pending sync_queue items.

Runs via system crontab every minute. Reads DATABASE_URL from environment.
Processes one batch per invocation and exits.
"""
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List

from dotenv import load_dotenv

_project_root = Path(__file__).resolve().parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

load_dotenv(_project_root / ".env")

import psycopg
from openai import OpenAI
from pgvector.psycopg import register_vector
from psycopg.rows import dict_row

logger = logging.getLogger("ramon.sync.worker")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)

BATCH_SIZE = int(os.environ.get("SYNC_BATCH_SIZE", "10"))


def _get_database_url() -> str:
    """Build DATABASE_URL from individual components or use existing value."""
    existing_url = os.environ.get("DATABASE_URL", "").strip()
    if existing_url:
        return existing_url

    return (
        f"postgresql://{os.environ['DB_USER']}:{os.environ['DB_PASSWORD']}"
        f"@{os.environ['DB_HOST']}:{os.environ['DB_PORT']}/{os.environ['DB_NAME']}"
    )


def _embedding_text(name: str, description: str, categories: str) -> str:
    """Build the text used for embedding from the three relevant fields."""
    return f"{name}\n{description}\n{categories}"


def _compute_embedding(fields: Dict[str, Any]) -> Any:
    """Compute an embedding vector for a product's text fields."""
    try:
        api_key = os.environ.get("OPENAI_API_KEY", "")
        if not api_key:
            logger.warning("OPENAI_API_KEY not set, skipping embedding")
            return None

        text = _embedding_text(
            fields.get("name", ""),
            fields.get("description", ""),
            fields.get("categories", ""),
        )
        if not text.strip():
            return None

        client = OpenAI(api_key=api_key)
        response = client.embeddings.create(
            input=text,
            model="text-embedding-3-small",
        )
        return response.data[0].embedding
    except Exception as exc:
        logger.exception("Failed to compute embedding: %s", exc)
        return None


def _upsert_product(conn, product_id: str, fields: Dict[str, Any]) -> None:
    """Upsert a product, recomputing the embedding only if needed."""
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            "SELECT name, description, categories FROM products "
            "WHERE product_id = %s",
            (product_id,),
        )
        existing = cur.fetchone()

    needs_embedding = True
    if existing is not None:
        old_text = _embedding_text(
            existing["name"] or "",
            existing["description"] or "",
            existing["categories"] or "",
        )
        new_text = _embedding_text(
            fields.get("name", ""),
            fields.get("description", ""),
            fields.get("categories", ""),
        )
        needs_embedding = old_text != new_text

    embedding_value = None
    if needs_embedding:
        embedding_value = _compute_embedding(fields)

    if embedding_value is not None:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO products (product_id, sku, name, description, categories,
                                      price, stock, in_stock, url, image_url, status,
                                      embedding, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s::vector, NOW())
                ON CONFLICT (product_id) DO UPDATE SET
                    sku = EXCLUDED.sku,
                    name = EXCLUDED.name,
                    description = EXCLUDED.description,
                    categories = EXCLUDED.categories,
                    price = EXCLUDED.price,
                    stock = EXCLUDED.stock,
                    in_stock = EXCLUDED.in_stock,
                    url = EXCLUDED.url,
                    image_url = EXCLUDED.image_url,
                    status = EXCLUDED.status,
                    embedding = EXCLUDED.embedding,
                    updated_at = NOW()
                """,
                (
                    product_id,
                    fields.get("sku", ""),
                    fields.get("name", ""),
                    fields.get("description", ""),
                    fields.get("categories", ""),
                    fields.get("price", 0.0),
                    fields.get("stock", 0),
                    fields.get("in_stock", True),
                    fields.get("url", ""),
                    fields.get("image_url", ""),
                    fields.get("status", "published"),
                    str(embedding_value),
                ),
            )
    else:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO products (product_id, sku, name, description, categories,
                                      price, stock, in_stock, url, image_url, status,
                                      updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
                ON CONFLICT (product_id) DO UPDATE SET
                    sku = EXCLUDED.sku,
                    name = EXCLUDED.name,
                    description = EXCLUDED.description,
                    categories = EXCLUDED.categories,
                    price = EXCLUDED.price,
                    stock = EXCLUDED.stock,
                    in_stock = EXCLUDED.in_stock,
                    url = EXCLUDED.url,
                    image_url = EXCLUDED.image_url,
                    status = EXCLUDED.status,
                    updated_at = NOW()
                """,
                (
                    product_id,
                    fields.get("sku", ""),
                    fields.get("name", ""),
                    fields.get("description", ""),
                    fields.get("categories", ""),
                    fields.get("price", 0.0),
                    fields.get("stock", 0),
                    fields.get("in_stock", True),
                    fields.get("url", ""),
                    fields.get("image_url", ""),
                    fields.get("status", "published"),
                ),
            )


def _delete_product(conn, product_id: str) -> None:
    """Delete a product by its external product_id."""
    with conn.cursor() as cur:
        cur.execute(
            "DELETE FROM products WHERE product_id = %s",
            (product_id,),
        )


def _process_pending_batch(batch_size: int = 50) -> dict:
    """Process a batch of pending sync_queue items.

    Returns:
        Summary dict with processed, upserted, deleted, errors counts.
    """
    db_url = _get_database_url()

    with psycopg.connect(db_url) as conn:
        register_vector(conn)
        conn.autocommit = False

        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                SELECT id, payload FROM sync_queue
                WHERE status = 'pending'
                ORDER BY created_at ASC
                LIMIT %s
                FOR UPDATE SKIP LOCKED
                """,
                (batch_size,),
            )
            rows = cur.fetchall()

        if not rows:
            return {"processed": 0, "upserted": 0, "deleted": 0, "errors": []}

        ids = [row["id"] for row in rows]
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE sync_queue SET status = 'processing' WHERE id = ANY(%s)",
                (ids,),
            )

        upserted = 0
        deleted = 0
        errors: List[str] = []

        for row in rows:
            payload = row["payload"]
            action = payload.get("action", "")
            product_id = payload.get("product_id", "")
            fields = payload.get("fields", {})

            try:
                if action == "delete":
                    _delete_product(conn, product_id)
                    deleted += 1
                elif action == "upsert":
                    _upsert_product(conn, product_id, fields)
                    upserted += 1
                else:
                    errors.append(f"Unknown action '{action}' for {product_id}")

                with conn.cursor() as cur:
                    cur.execute(
                        "UPDATE sync_queue SET status = 'done', processed_at = NOW() WHERE id = %s",
                        (row["id"],),
                    )
            except Exception as exc:
                msg = f"Product {product_id}: {exc}"
                logger.exception(msg)
                errors.append(msg)
                with conn.cursor() as cur:
                    cur.execute(
                        "UPDATE sync_queue SET status = 'error', error = %s WHERE id = %s",
                        (msg, row["id"]),
                    )

        conn.commit()

    logger.info(
        "Worker batch: processed=%d, upserted=%d, deleted=%d, errors=%d",
        len(rows), upserted, deleted, len(errors),
    )
    return {
        "processed": len(rows),
        "upserted": upserted,
        "deleted": deleted,
        "errors": errors,
    }


def main() -> None:
    """Process one batch of pending sync items."""
    result = _process_pending_batch(batch_size=BATCH_SIZE)

    if result["errors"]:
        logger.warning(
            "Batch completed with errors: %s", "; ".join(result["errors"])
        )

    if result["processed"] > 0:
        logger.info(
            "Processed %d items (upserted=%d, deleted=%d)",
            result["processed"],
            result["upserted"],
            result["deleted"],
        )


if __name__ == "__main__":
    main()
