"""
Add in_stock boolean column to products table.

WooCommerce tracks both numeric stock quantity and a stock status (instock/outofstock).
This column captures the stock status for products with unmanaged inventory.
"""
from yoyo import step

__depends__ = {"0001_initial_schema"}

steps = [
    step(
        "ALTER TABLE products ADD COLUMN in_stock BOOLEAN DEFAULT true",
        "ALTER TABLE products DROP COLUMN IF EXISTS in_stock",
    ),
]
