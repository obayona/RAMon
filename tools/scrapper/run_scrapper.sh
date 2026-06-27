#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "========================================"
echo "  PlanetCA Product Scraper"
echo "========================================"
echo ""

python3 -c "import requests" 2>/dev/null || {
    echo "[!] 'requests' module missing."
    echo "    Install: pip3 install requests"
    exit 1
}

echo "[*] Running scraper..."
echo ""
PYTHONUNBUFFERED=1 python3 -u scraper.py
echo ""
echo "[*] Done. See $(pwd)/products.txt"
