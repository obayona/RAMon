#!/usr/bin/env python3
"""Scraper for planetca.com.ve — two-phase scraper.

Phase 1: Scrape shop listing pages for product IDs, names, URLs, categories.
Phase 2: Visit each individual product page for SKU, description, rating, reviews.
Output: CSV with all fields.
"""

import re
import csv
import random
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests

BASE_URL = "https://www.planetca.com.ve"
SHOP_URL = f"{BASE_URL}/tienda/"
OUTPUT_FILE = Path(__file__).parent / "products.csv"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}
TARGET_COUNT = 100
PARALLEL_WORKERS = 8

# ---------------------------------------------------------------------------
# Phase 1 — parse listing pages
# ---------------------------------------------------------------------------

PRODUCT_CARD_RE = re.compile(
    r'<li\s+class="product-wrap">\s*'
    r'<div\s+class="product-loop\s[^"]*?post-(\d+)[^"]*?"[^>]*>'
    r'.*?'
    r'woocommerce-loop-product__title[^>]*>'
    r'<a\s+href="([^"]+)"[^>]*>'
    r'([^<]+)'
    r'</a>',
    re.DOTALL
)


def get_total_pages(html):
    m = re.search(r"(\d+)–(\d+) de (\d+)", html)
    if m:
        total = int(m.group(3))
        return (total + 47) // 48, total
    return 1, 0


def parse_listing(html):
    products = []
    for m in PRODUCT_CARD_RE.finditer(html):
        pid, url, name = m.group(1), m.group(2), m.group(3).strip()
        loop_start = max(0, m.start() - 300)
        loop_html = html[loop_start:m.end()]
        cats = []
        for c in re.finditer(r'product_cat-([^\s"]+)', loop_html):
            cn = c.group(1).replace("-", " ").title()
            if cn not in cats:
                cats.append(cn)
        products.append({"id": pid, "name": name, "url": url, "categories": cats})
    return products


def fetch_listing(page):
    url = f"{BASE_URL}/tienda/page/{page}/" if page > 1 else SHOP_URL
    try:
        r = requests.get(url, headers=HEADERS, timeout=20)
        r.raise_for_status()
        return parse_listing(r.text)
    except requests.RequestException:
        return []


def phase1_collect_products():
    """Scrape listing pages and return deduplicated product list."""
    r = requests.get(SHOP_URL, headers=HEADERS, timeout=15)
    r.raise_for_status()
    total_pages, total = get_total_pages(r.text)
    print(f"[+] {total} products across {total_pages} pages")

    all_products = parse_listing(r.text)
    print(f"[+] Page 1: {len(all_products)} products")

    remaining = [p for p in range(2, total_pages + 1)]
    sample = sorted(random.sample(remaining, min(len(remaining), 15)))

    with ThreadPoolExecutor(max_workers=6) as ex:
        futures = {ex.submit(fetch_listing, p): p for p in sample}
        for f in as_completed(futures):
            page = futures[f]
            products = f.result()
            print(f"  [-] Page {page}: {len(products)} products")
            all_products.extend(products)

    seen = set()
    unique = []
    for p in all_products:
        if p["url"] not in seen:
            seen.add(p["url"])
            unique.append(p)

    random.shuffle(unique)
    selected = unique[:TARGET_COUNT]
    print(f"[+] Phase 1 done — {len(selected)} unique products selected")
    return selected


# ---------------------------------------------------------------------------
# Phase 2 — enrich from individual product pages
# ---------------------------------------------------------------------------

def parse_product_page(url, timeout=15):
    """Fetch a product page and extract SKU, description, rating, reviews."""
    try:
        r = requests.get(url, headers=HEADERS, timeout=timeout)
        r.raise_for_status()
    except requests.RequestException:
        return {}

    html = r.text
    result = {}

    # SKU
    m = re.search(r'<span class="sku">\s*([^<]+?)\s*</span>', html)
    result["sku"] = m.group(1).strip() if m else ""

    # Rating number (from star-rating)
    m = re.search(
        r'<strong\s+class="rating"[^>]*>([\d.]+)</strong>',
        html
    )
    result["rating"] = m.group(1) if m else ""

    # Review count (from review link)
    m = re.search(
        r'class="woocommerce-review-link[^"]*"[^>]*>\s*\(\s*(\d+)\s*',
        html
    )
    result["reviews"] = m.group(1) if m else "0"

    # Description from the description tab — stop before the next tab starts
    m = re.search(
        r'id="tab-description"[^>]*>\s*([\s\S]*?)(?=\s*</div>\s*</div>\s*<div\s+class="card")',
        html
    )
    if m:
        desc = re.sub(r'<[^>]+>', '', m.group(1)).strip()
        desc = re.sub(r'^Descripción\s*', '', desc).strip()
        result["description"] = desc
    else:
        result["description"] = ""

    return result


def phase2_enrich(products):
    """Fetch details for each product page in parallel."""
    print(f"[+] Phase 2 — enriching {len(products)} products...")

    with ThreadPoolExecutor(max_workers=PARALLEL_WORKERS) as ex:
        fut_map = {ex.submit(parse_product_page, p["url"]): p for p in products}
        done = 0
        for f in as_completed(fut_map):
            p = fut_map[f]
            data = f.result()
            p["sku"] = data.get("sku", "")
            p["rating"] = data.get("rating", "")
            p["reviews"] = data.get("reviews", "0")
            p["description"] = data.get("description", "")
            done += 1
            if done % 20 == 0:
                print(f"    [{done}/{len(products)}]")

    print(f"[+] Phase 2 done")
    return products


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

def write_csv(products):
    fieldnames = ["id", "name", "url", "categories", "sku", "rating", "reviews", "description"]
    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for p in products:
            writer.writerow({
                "id": p["id"],
                "name": p["name"],
                "url": p["url"],
                "categories": "; ".join(p["categories"]),
                "sku": p.get("sku", ""),
                "rating": p.get("rating", ""),
                "reviews": p.get("reviews", "0"),
                "description": p.get("description", ""),
            })
    print(f"[+] CSV written to {OUTPUT_FILE}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    products = phase1_collect_products()
    products = phase2_enrich(products)
    write_csv(products)
    for p in products[:5]:
        print(f"    \u2022 {p['name'][:50]} | rating={p.get('rating','?')} rev={p.get('reviews','?')}")
    print(f"[+] Done — {len(products)} products")


if __name__ == "__main__":
    main()
