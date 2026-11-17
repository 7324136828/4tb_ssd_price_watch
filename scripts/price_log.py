"""Shared helpers for reading, validating and appending rows to prices.csv.

Used by the scripts/track_*.py trackers and scripts/add_price.py. Standard library only.

The rules mirror claude.md:
  * 10-column schema, lowercase condition, numeric price, ISO dates.
  * A price of any age may be logged; source_date only has to be a real
    date that is not after the run date.
  * One row per (date, category, item, store, condition); repeated runs on
    the same day never duplicate a row.
"""
import csv
import datetime as dt
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CSV_PATH = ROOT / "prices.csv"

FIELDS = ["date", "category", "item", "spec", "store", "condition",
          "price_usd", "basis", "source_date", "url"]
CATEGORIES = ("ssd", "ram", "nvidia_gpu", "amd_gpu", "egpu", "macbook")
CONDITIONS = ("new", "used", "refurbished")
APPROVED_STORES = ("Amazon", "eBay", "Newegg", "Best Buy", "Walmart",
                   "B&H Photo", "Micro Center", "Apple")

def parse_date(value):
    return dt.date.fromisoformat(str(value).strip())


def not_in_future(source_date, run_date):
    """True when source_date <= run_date (there is no lower age limit)."""
    return parse_date(source_date) <= parse_date(run_date)


def dedupe_key(row):
    return (row["date"], row["category"], row["item"].strip().lower(),
            row["store"].strip().lower(), row["condition"])


def validate_row(row, run_date=None):
    """Return a list of problems with row (empty list means the row is valid)."""
    problems = []
    missing = [f for f in FIELDS if not str(row.get(f, "")).strip()]
    if missing:
        problems.append(f"missing fields: {', '.join(missing)}")
        return problems
    if row["category"] not in CATEGORIES:
        problems.append(f"category must be one of {', '.join(CATEGORIES)}")
    if row["condition"] not in CONDITIONS:
        problems.append(f"condition must be lowercase {'/'.join(CONDITIONS)}")
    if not any(row["store"].startswith(s) for s in APPROVED_STORES):
        problems.append(f"store must start with one of {', '.join(APPROVED_STORES)}")
    try:
        price = float(row["price_usd"])
        if price <= 0:
            problems.append("price_usd must be positive")
    except ValueError:
        problems.append("price_usd must be a plain number like 475.00")
    if not (row["basis"] == "direct" or
            (row["basis"].startswith("reported (") and row["basis"].endswith(")"))):
        problems.append("basis must be 'direct' or 'reported (<Source Name>)'")
    if not row["url"].startswith(("http://", "https://")):
        problems.append("url must start with http:// or https://")
    try:
        parse_date(row["date"])
        parse_date(row["source_date"])
        if not not_in_future(row["source_date"], run_date or row["date"]):
            problems.append(f"source_date {row['source_date']} is after run date "
                            f"{run_date or row['date']}")
    except ValueError:
        problems.append("date and source_date must be YYYY-MM-DD")
    if row["category"] == "ssd" and "TB" not in row["spec"].upper():
        problems.append("ssd spec must include the capacity, e.g. '4TB TLC'")
    return problems


def read_rows(path=CSV_PATH):
    if not Path(path).exists():
        return []
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def format_price(value):
    return f"{float(value):.2f}"


def append_rows(rows, path=CSV_PATH):
    """Append rows that are not already logged. Returns (added, skipped_duplicates)."""
    path = Path(path)
    seen = {dedupe_key(r) for r in read_rows(path)}
    added, dupes = [], []
    for row in rows:
        row = {f: str(row[f]).strip() for f in FIELDS}
        row["price_usd"] = format_price(row["price_usd"])
        key = dedupe_key(row)
        if key in seen:
            dupes.append(row)
            continue
        seen.add(key)
        added.append(row)
    if added:
        new_file = not path.exists() or path.stat().st_size == 0
        # Make sure we start on a fresh line even if the file lacks a trailing newline.
        if not new_file:
            with path.open("rb") as f:
                f.seek(-1, 2)
                needs_newline = f.read(1) != b"\n"
        with path.open("a", newline="", encoding="utf-8") as f:
            if not new_file and needs_newline:
                f.write("\n")
            writer = csv.DictWriter(f, fieldnames=FIELDS, lineterminator="\n")
            if new_file:
                writer.writeheader()
            writer.writerows(added)
    return added, dupes
