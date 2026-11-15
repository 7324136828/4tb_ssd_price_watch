#!/usr/bin/env python3
"""Append one hand-checked price to prices.csv, with the same checks as the tracker.

Use it for prices the automatic tracker cannot log: RTX 4090 / 3090 / 3090 Ti
and RX 7900 XT (not covered by the source), verified eBay used listings, RAM,
SSDs and eGPUs.

Examples:
    python scripts/add_price.py nvidia_gpu "RTX 4090 (MSI Gaming X Trio)" "24GB GDDR6X" \\
        "eBay" used 1899.00 "https://www.ebay.com/itm/123" --source-date 2026-11-15
    python scripts/add_price.py amd_gpu "RX 7900 XT (Sapphire Pulse)" "20GB GDDR6" \\
        Newegg new 649.99 "https://www.newegg.com/p/..." --basis "reported (9to5Toys)"

Rows with the wrong category/condition, a store that is not approved, or a
source_date outside the 2-day window are refused. A row already logged today
for the same item, store and condition is skipped.
"""
import argparse
import datetime as dt
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import price_log  # noqa: E402


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter,
                                 epilog=__doc__.split("\n\n", 1)[1])
    ap.add_argument("category", choices=price_log.CATEGORIES)
    ap.add_argument("item", help='normalized name, e.g. "RTX 4090 (ASUS TUF Gaming OC)"')
    ap.add_argument("spec", help='e.g. "24GB GDDR6X", "4TB TLC", "1x64GB DDR5-5600 CL46"')
    ap.add_argument("store", help=f"one of: {', '.join(price_log.APPROVED_STORES)} "
                    "(a suffix such as ' (third-party seller)' is allowed)")
    ap.add_argument("condition", choices=price_log.CONDITIONS)
    ap.add_argument("price", help="price in USD, e.g. 1899.00 ($ and commas are stripped)")
    ap.add_argument("url")
    ap.add_argument("--basis", default="direct",
                    help="'direct' (default) or 'reported (<Source Name>)'")
    ap.add_argument("--date", default=dt.date.today().isoformat(), help="run date (default today)")
    ap.add_argument("--source-date", help="date the price was seen (default: run date)")
    ap.add_argument("--csv", default=str(price_log.CSV_PATH))
    ap.add_argument("--dry-run", action="store_true", help="validate only, do not write")
    args = ap.parse_args(argv)

    row = {
        "date": args.date, "category": args.category, "item": args.item,
        "spec": args.spec, "store": args.store, "condition": args.condition,
        "price_usd": args.price.replace("$", "").replace(",", ""),
        "basis": args.basis, "source_date": args.source_date or args.date, "url": args.url,
    }
    problems = price_log.validate_row(row, args.date)
    if problems:
        for p in problems:
            print(f"error: {p}", file=sys.stderr)
        return 2
    if args.dry_run:
        print("Row is valid (dry run, nothing written).")
        return 0
    added, dupes = price_log.append_rows([row], args.csv)
    if dupes:
        print("Already logged today for this item, store and condition; nothing written.")
    else:
        print(f"Added: {added[0]['item']} {added[0]['store']} {added[0]['condition']} "
              f"${added[0]['price_usd']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
