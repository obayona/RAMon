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
