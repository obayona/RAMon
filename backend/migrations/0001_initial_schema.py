"""
Initial database schema for RAMon Chatbot.
Creates the products table with pgvector support.
"""
from yoyo import step

__depends__ = {}

steps = [
    # Enable required extensions
    step(
        "CREATE EXTENSION IF NOT EXISTS vector",
        "DROP EXTENSION IF EXISTS vector",
        ignore_errors="apply",
    ),
    step(
        'CREATE EXTENSION IF NOT EXISTS "uuid-ossp"',
        'DROP EXTENSION IF EXISTS "uuid-ossp"',
        ignore_errors="apply",
    ),
    
    # Products table
    step(
        """
        CREATE TABLE products (
            id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
            product_id TEXT,
            sku TEXT,
            name TEXT NOT NULL,
            description TEXT DEFAULT '',
            categories TEXT DEFAULT '',
            price DOUBLE PRECISION DEFAULT 0.0,
            stock INTEGER DEFAULT 0,
            embedding VECTOR(1536)
        )
        """,
        "DROP TABLE IF EXISTS products",
    ),
    
    # Indexes
    step(
        "CREATE INDEX idx_products_id ON products(product_id)",
        "DROP INDEX IF EXISTS idx_products_id",
    ),
    step(
        "CREATE INDEX idx_products_price ON products(price)",
        "DROP INDEX IF EXISTS idx_products_price",
    ),
    
    # HNSW index for vector similarity search
    step(
        "CREATE INDEX idx_products_embedding ON products USING hnsw (embedding vector_cosine_ops)",
        "DROP INDEX IF EXISTS idx_products_embedding",
    ),
]
