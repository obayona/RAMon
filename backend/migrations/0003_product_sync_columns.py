"""
Extend products table with sync support columns.
Adds url, image_url, status, updated_at, and a unique constraint on product_id.
"""
from yoyo import step

__depends__ = {"0001_initial_schema"}

steps = [
    step(
        "ALTER TABLE products ADD COLUMN url TEXT DEFAULT ''",
        "ALTER TABLE products DROP COLUMN IF EXISTS url",
    ),
    step(
        "ALTER TABLE products ADD COLUMN image_url TEXT DEFAULT ''",
        "ALTER TABLE products DROP COLUMN IF EXISTS image_url",
    ),
    step(
        "ALTER TABLE products ADD COLUMN status TEXT DEFAULT 'publish'",
        "ALTER TABLE products DROP COLUMN IF EXISTS status",
    ),
    step(
        "ALTER TABLE products ADD COLUMN updated_at TIMESTAMPTZ DEFAULT NOW()",
        "ALTER TABLE products DROP COLUMN IF EXISTS updated_at",
    ),
    step(
        "ALTER TABLE products ADD CONSTRAINT uq_products_product_id UNIQUE (product_id)",
        "ALTER TABLE products DROP CONSTRAINT IF EXISTS uq_products_product_id",
    ),
    step(
        "CREATE INDEX idx_products_status ON products(status)",
        "DROP INDEX IF EXISTS idx_products_status",
    ),
]
