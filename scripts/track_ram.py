#!/usr/bin/env python3
"""Track single 64 GB DDR5 SO-DIMM modules and append rows to prices.csv.

Source: the Amazon product page of each module in MODULES (a direct store
check). Each page gives the title, the buy-box price, the stock message and
the seller.

Rules applied (see claude.md):
  * Only single 1x64GB DDR5 SO-DIMM modules at 5600 MT/s or faster. The page
    title must contain the module's part number, so a re-used listing for a
    different product is never logged.
  * Only in-stock listings with a price.
  * A seller other than Amazon is logged as "Amazon (third-party seller)".

To track another module, add its Amazon ASIN, part number and spec to MODULES.

Usage:
    python scripts/track_ram.py            # dry run: print what would be logged
    python scripts/track_ram.py --write    # append new rows to prices.csv
"""
import argparse
import datetime as dt
import html
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import price_log  # noqa: E402
from track_gpus import fetch  # noqa: E402

PRODUCT_URL = "https://www.amazon.com/dp/{asin}"

# asin, item (brand + part number, as used in prices.csv), part number, spec
MODULES = [
    ("B0DSQWZ5G2", "Crucial CT64G56C46S5", "CT64G56C46S5", "1x64GB DDR5-5600 CL46"),
    ("B0G7RLK95V", "G.Skill F5-5600S4645A64GX1-RS", "F5-5600S4645A64GX1-RS",
     "1x64GB DDR5-5600 CL46"),
]


def _text(fragment):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", fragment))).strip()


def parse_product_page(page_html):
    """Return {"title", "price", "availability", "seller"} from an Amazon product page.

    Missing parts are "" (text) or None (price).
    """
    title = re.search(r'id="productTitle"[^>]*>(.*?)</span>', page_html, re.S)
    price = re.search(r'id="corePrice_feature_div".{0,1500}?class="a-offscreen">\s*\$([\d,]+\.\d{2})',
                      page_html, re.S)
    if not price:
        price = re.search(r'"priceAmount":\s*(\d+(?:\.\d+)?)', page_html)
    avail = re.search(r'id="availability"[^>]*>(.*?)</div>', page_html, re.S)
    seller = re.search(r'id="sellerProfileTriggerId"[^>]*>([^<]*)<', page_html)
    if not seller:
        seller = re.search(r'id="merchantInfoFeature_feature_div".{0,2500}?'
                           r'offer-display-feature-text-message">([^<]*)<', page_html, re.S)
    return {
        "title": _text(title.group(1)) if title else "",
        "price": float(price.group(1).replace(",", "")) if price else None,
        "availability": _text(avail.group(1)) if avail else "",
        "seller": _text(seller.group(1)) if seller else "",
    }


def in_stock(availability):
    low = availability.lower()
    return "in stock" in low and "out of stock" not in low


def evaluate(page, asin, item, part_number, spec, run_date):
    """Return (row, None) when the page qualifies, else (None, reason)."""
    if part_number.lower() not in page["title"].lower():
        return None, f"page title does not mention {part_number}"
    if not page["price"]:
        return None, "no price"
    if not in_stock(page["availability"]):
        return None, f"not in stock ({page['availability'] or 'no stock message'})"
    seller = page["seller"].lower()
    store = "Amazon" if seller in ("", "amazon.com", "amazon") else "Amazon (third-party seller)"
    return {
        "date": run_date, "category": "ram", "item": item, "spec": spec,
        "store": store, "condition": "new",
        "price_usd": price_log.format_price(page["price"]),
        "basis": "direct", "source_date": run_date,
        "url": PRODUCT_URL.format(asin=asin),
    }, None


def track(run_date):
    report = {"run_date": run_date, "rows": [], "skipped": [], "errors": []}
    for i, (asin, item, part_number, spec) in enumerate(MODULES):
        if i:
            time.sleep(2)
        status, body = fetch(PRODUCT_URL.format(asin=asin))
        if status != 200:
            report["errors"].append(f"{item}: fetch failed (status {status})")
            continue
        page = parse_product_page(body)
        if not page["title"]:
            report["errors"].append(f"{item}: no product page returned (blocked or captcha)")
            continue
        row, reason = evaluate(page, asin, item, part_number, spec, run_date)
        if row:
            report["rows"].append(row)
        else:
            report["skipped"].append({"listing": item, "reason": reason})
    return report


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--write", action="store_true", help="append qualifying rows to prices.csv")
    ap.add_argument("--date", default=dt.date.today().isoformat(),
                    help="run date YYYY-MM-DD (default: today)")
    ap.add_argument("--csv", default=str(price_log.CSV_PATH), help="path to prices.csv")
    args = ap.parse_args(argv)

    price_log.parse_date(args.date)
    report = track(args.date)

    print(f"\nRAM price check for {report['run_date']} (source: Amazon product pages)")
    print("\nQualifying prices:")
    for r in report["rows"]:
        print(f"  {r['item']:<32} {r['store']:<28} ${float(r['price_usd']):>9,.2f}")
    if not report["rows"]:
        print("  none")
    if args.write:
        rows = [r for r in report["rows"] if not price_log.validate_row(r, args.date)]
        added, dupes = price_log.append_rows(rows, args.csv)
        print(f"\nWrote {len(added)} new row(s) to prices.csv; {len(dupes)} already logged today.")
    if report["skipped"]:
        print("\nNot logged:")
        for s in report["skipped"]:
            print(f"  {s['listing']}: {s['reason']}")
    if report["errors"]:
        print("\nErrors:")
        for e in report["errors"]:
            print(f"  {e}")
    return 1 if report["errors"] and not report["rows"] else 0


if __name__ == "__main__":
    sys.exit(main())
