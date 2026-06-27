# RAMon — Tools

## Project Overview

Scrapper for https://www.planetca.com.ve/tienda website. It downloads products on a products_processed.csv file

Python 3.12.3. Virtual env at `scrapper/venv/`.

---

## Build / Lint / Test Commands

No test framework or linter is configured yet. The following conventions apply:

```bash
# Run the scraper (from scrapper/)
python3 scraper.py                                # full run
PYTHONUNBUFFERED=1 python3 -u scraper.py           # unbuffered output

# Run the post-processing script
python3 process_products.py

# Run via shell script
./run_scrapper.sh

# Activate venv
source scrapper/venv/bin/activate

# Manual checks to validate code before committing
python3 -m py_compile scraper/scraper.py           # syntax check
python3 -c "import scraper.scraper"               # import check
```

When adding tests, place them in a `tests/` directory parallel to the module and use `unittest` or `pytest` (no preference yet). Run with:
```bash
python3 -m pytest tests/                          # all tests
python3 -m pytest tests/test_foo.py               # single file
python3 -m pytest tests/test_foo.py::test_bar     # single test
```

---

## Code Style Guidelines

### Imports

Order: standard library → third-party → local. Separate groups with a blank line.

```python
import csv
import re
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

import requests
```

### Formatting

- No formatter (black/isort/ruff) configured. Follow existing style:
  - Single blank line between top-level definitions
  - Two blank lines before class definitions
  - 99-character line length (existing convention)
  - No trailing whitespace

### Types

- Use type hints for function parameters and return values (Python 3.12 syntax allowed)
- Prefer `str` over `:class:` annotations
- `Optional[X]` for nullable values, not `X | None` (existing convention looks toward positional)

```python
def clean_description(text: str) -> str: ...
def fetch_listing(page: int) -> list[dict]: ...
```

### Naming

| Kind | Convention | Example |
|------|-----------|---------|
| Constants | `UPPER_CASE` | `TARGET_COUNT = 100` |
| Functions | `snake_case` | `parse_listing()` |
| Variables | `snake_case` | `total_pages` |
| Modules | `snake_case` | `scraper.py` |
| Classes (future) | `PascalCase` | `ProductScraper` |

### Error Handling

- Always wrap I/O and network calls in try/except
- Graceful degradation: return empty container (`[]`, `{}`, `""`) on failure, never `None`
- Raise for truly unexpected errors; suppress expected transient failures at the call site
- Check dependencies at script startup when run directly:

```python
python3 -c "import requests" 2>/dev/null || { echo "Install: pip3 install requests"; exit 1; }
```

### File Paths

Always resolve relative to the script location:

```python
from pathlib import Path
OUTPUT = Path(__file__).parent / "products.csv"
```

### CSV I/O

- Use `csv.DictReader` / `csv.DictWriter` (not manual string formatting)
- Always pass `newline=""` and `encoding="utf-8"` to `open()`
- Multi-line fields (descriptions) are handled by CSV quoting — do not strip newlines manually

### Shell Scripts

- Shebang: `#!/bin/bash`
- Always `set -e` at the top
- Resolve script dir: `SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"`
- Check required commands/tools before running

### Parallelism

Use `concurrent.futures.ThreadPoolExecutor` with `as_completed`:

```python
with ThreadPoolExecutor(max_workers=8) as ex:
    fut_map = {ex.submit(fetch, arg): item for item in items}
    for f in as_completed(fut_map):
        item = fut_map[f]
        result = f.result()
```

### Regex

- Compile with `re.compile()` at module level for reuse
- Use `re.DOTALL` when matching across lines
- Capture groups by index or name; always guard with `if m:` or `.get()`

### main Guard

```python
def main():
    ...

if __name__ == "__main__":
    main()
```

### Logging

Use `print()` with prefix markers:
- `[+]` for success/progress
- `[-]` for detail/sub-steps
- `[!]` for warnings

---

## Environment

- Python 3.12.3 — no .python-version file yet
- Virtual env: `scrapper/venv/`
- Dependencies: `requests` (install with `pip3 install requests` inside venv)
- `.env` at repo root contains `PINECONE_API_KEY` — do not commit, do not log
