#!/usr/bin/env python3
"""Clean up products.csv and produce products_processed.csv.

- Truncates descriptions at "Valoraciones" (removes embedded review/rating HTML junk)
- Strips leading/trailing whitespace from each line
- Removes empty lines
"""

import csv
from pathlib import Path

INPUT = Path(__file__).parent / "products.csv"
OUTPUT = Path(__file__).parent / "products_processed.csv"


def clean_description(text: str) -> str:
    idx = text.find("Valoraciones")
    if idx != -1:
        text = text[:idx]
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    return "\n".join(lines)


def main():
    with open(INPUT, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)

    for row in rows:
        row["description"] = clean_description(row["description"])

    with open(OUTPUT, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} rows to {OUTPUT}")


if __name__ == "__main__":
    main()
