#!/usr/bin/env python3
"""Track high-memory MacBooks (48 GB RAM and up) and append rows to prices.csv.

Sources, both direct store checks:
  * Apple Certified Refurbished: the refurbished Mac page lists every unit in
    stock with its memory, storage and price.
  * Amazon: one search per memory level in RAM_LEVELS finds the listings; the
    product page of the cheapest listing of each configuration then gives the
    price, the stock message and the seller that are logged.

One price series is kept per model, screen size, chip and memory level, e.g.
"MacBook Pro 16 M5 Max 64GB". For each series the script logs the cheapest
unit per store and condition; that unit's storage and core counts go in spec,
so the storage can differ from one day to the next.

Rules applied (see claude.md):
  * Only MacBooks whose memory is one of RAM_LEVELS. A title that names two
    memory sizes, or no screen size or chip, is skipped as ambiguous.
  * Amazon: only in-stock listings with a price. "Renewed" listings are logged
    as refurbished, and a seller other than Amazon as
    "Amazon (third-party seller)".

Apple's own price for a new custom-memory order is not read by this script
(the store only shows it inside the configurator); log it by hand with
scripts/add_price.py. eBay listings come from scripts/track_ebay.py, which
uses parse_config and the naming helpers below.

Usage:
    python scripts/track_macbooks.py            # dry run: print what would be logged
    python scripts/track_macbooks.py --write    # append new rows to prices.csv
    python scripts/track_macbooks.py --source apple   # only one source (apple, amazon)
"""
import argparse
import datetime as dt
import html
import json
import re
import sys
import time
import urllib.parse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import price_log  # noqa: E402
from track_gpus import fetch  # noqa: E402
from track_ram import PRODUCT_URL, in_stock, parse_product_page  # noqa: E402

CATEGORY = "macbook"
RAM_LEVELS = (48, 64, 96, 128)  # GB of unified memory worth tracking

APPLE_URL = "https://www.apple.com"
REFURB_URL = APPLE_URL + "/shop/refurbished/mac"
REFURB_STORE = "Apple (Certified Refurbished)"
AMAZON_SEARCH_URL = "https://www.amazon.com/s?k={query}"
AMAZON_QUERY = "macbook pro {ram}gb"
AMAZON_TRIES = 2  # product pages opened per configuration before giving up

# Every memory size Apple has sold in an Apple-silicon MacBook, and the GB
# figures that are storage, not memory.
MEMORY_SIZES = {8, 16, 18, 24, 32, 36, 48, 64, 96, 128}
STORAGE_GB = {256, 512}

LINE_RE = re.compile(r"\bMacBook\s+(Pro|Air)\b", re.IGNORECASE)
SIZE_RE = re.compile(r"(?<![\d.])(1[3-6])(?:\.\d)?\s*-?\s*(?:inch\b|in\b|\"|”)", re.IGNORECASE)
CHIP_RE = re.compile(r"\bM(\d)(?:\s*(Pro|Max))?\b", re.IGNORECASE)
GB_RE = re.compile(r"(?<![\d.])(\d+)\s*GB\b", re.IGNORECASE)
TB_RE = re.compile(r"(?<![\d.])(\d+)\s*TB\b", re.IGNORECASE)
CORES_RE = re.compile(r"(\d+)\s*-?\s*core\s+(CPU|GPU)", re.IGNORECASE)
ACCESSORY_RE = re.compile(
    r"\b(case|cover|skin|sleeve|charger|protector|compatible with|for (apple )?macbook|"
    r"hub|dock|docking|stand|bundle|logic board|motherboard|top case|bottom case|palmrest|"
    r"lcd|replacement|screen (only|assembly)|display assembly)\b", re.IGNORECASE)
CONDITION_RES = (
    ("refurbished", re.compile(r"\b(renewed|refurbished|refurb)\b", re.IGNORECASE)),
    ("used", re.compile(r"\b(used|pre-?owned|open[- ]box)\b", re.IGNORECASE)),
)


def _clean(text):
    """Plain one-line text: tags and entities removed, odd hyphens made ASCII."""
    text = html.unescape(re.sub(r"<[^>]+>", " ", text or ""))
    text = re.sub(r"[‐-―]", "-", text).replace(" ", " ")
    return re.sub(r"\s+", " ", text).strip()


def parse_config(title):
    """Return (config, None) for a MacBook listing title, else (None, reason).

    config has line, size, chip, ram, storage ("" when the title gives none),
    cpu and gpu (core counts, "" when unknown) and condition.
    """
    title = _clean(title)
    line = LINE_RE.search(title)
    if not line:
        return None, "not a MacBook Pro or MacBook Air"
    if ACCESSORY_RE.search(title):
        return None, "accessory, part or bundle listing"
    size = SIZE_RE.search(title)
    if not size:
        return None, "no screen size in title"
    chips = {(n, (tier or "").title()) for n, tier in CHIP_RE.findall(title)}
    if len(chips) != 1:
        return None, "no chip in title" if not chips else "more than one chip in title"
    gb = {int(n) for n in GB_RE.findall(title)}
    memory = gb & MEMORY_SIZES
    if len(memory) != 1:
        return None, "no memory size in title" if not memory else "more than one memory size in title"
    storage = {f"{n}TB" for n in TB_RE.findall(title)} | {f"{n}GB" for n in gb & STORAGE_GB}
    if len(storage) > 1:
        return None, "more than one storage size in title"
    cores = {kind.upper(): count for count, kind in CORES_RE.findall(title)}
    number, tier = next(iter(chips))
    return {
        "line": f"MacBook {line.group(1).title()}", "size": int(size.group(1)),
        "chip": f"M{number} {tier}".strip(), "ram": memory.pop(),
        "storage": storage.pop() if storage else "",
        "cpu": cores.get("CPU", ""), "gpu": cores.get("GPU", ""),
        "condition": next((c for c, rx in CONDITION_RES if rx.search(title)), "new"),
    }, None


def item_name(config):
    return f"{config['line']} {config['size']} {config['chip']} {config['ram']}GB"


def spec_text(config):
    parts = [f"{config['ram']}GB RAM"]
    if config["storage"]:
        parts.append(f"{config['storage']} SSD")
    if config["cpu"] and config["gpu"]:
        parts.append(f"{config['cpu']}C CPU/{config['gpu']}C GPU")
    return ", ".join(parts)


def make_row(config, store, condition, price, url, run_date):
    return {
        "date": run_date, "category": CATEGORY, "item": item_name(config),
        "spec": spec_text(config), "store": store, "condition": condition,
        "price_usd": price_log.format_price(price), "basis": "direct",
        "source_date": run_date, "url": url,
    }


def cheapest_rows(rows):
    """Keep the lowest-priced row of each (item, store, condition)."""
    best = {}
    for row in rows:
        key = (row["item"], row["store"], row["condition"])
        if key not in best or float(row["price_usd"]) < float(best[key]["price_usd"]):
            best[key] = row
    return sorted(best.values(), key=lambda r: (r["item"], r["store"], r["condition"]))


# ---- Apple Certified Refurbished ------------------------------------------

def parse_refurb_page(page_html):
    """Return the list of product tiles embedded in Apple's refurbished page."""
    marker = re.search(r"REFURB_GRID_BOOTSTRAP\s*=\s*", page_html)
    if not marker:
        return None
    try:
        data, _ = json.JSONDecoder().raw_decode(page_html, marker.end())
    except ValueError:
        return None
    return data.get("tiles") or []


def refurb_row(tile, run_date):
    """Return (row, None) for a qualifying refurbished MacBook tile, else (None, reason)."""
    dims = (tile.get("filters") or {}).get("dimensions") or {}
    if dims.get("refurbClearModel") not in ("macbookpro", "macbookair"):
        return None, None  # another Mac or a display: not worth reporting
    title = _clean(tile.get("title"))
    memory = re.fullmatch(r"(\d+)gb", dims.get("tsMemorySize") or "")
    if not memory:
        return None, "no memory size"
    if int(memory.group(1)) not in RAM_LEVELS:
        return None, None
    # The tile's own fields are exact, so they are added to the title before parsing.
    described = (f"{title}, {dims.get('dimensionScreensize', '').replace('inch', '-inch')}, "
                 f"{memory.group(1)}GB, {(dims.get('dimensionCapacity') or '').upper()}")
    config, reason = parse_config(described)
    if not config:
        return None, reason
    try:
        price = float(tile["price"]["currentPrice"]["raw_amount"])
    except (KeyError, TypeError, ValueError):
        return None, "no price"
    url = APPLE_URL + (tile.get("productDetailsUrl") or "").split("?")[0]
    return make_row(config, REFURB_STORE, "refurbished", price, url, run_date), None


def track_apple(run_date, report):
    status, body = fetch(REFURB_URL)
    if status != 200:
        report["errors"].append(f"Apple refurbished page: fetch failed (status {status})")
        return
    tiles = parse_refurb_page(body)
    if tiles is None:
        report["errors"].append("Apple refurbished page: product data not found (page changed?)")
        return
    rows = []
    for tile in tiles:
        row, reason = refurb_row(tile, run_date)
        if row:
            rows.append(row)
        elif reason:
            report["skipped"].append({"listing": _clean(tile.get("title"))[:80], "reason": reason})
    report["rows"].extend(cheapest_rows(rows))


# ---- Amazon -----------------------------------------------------------------

def parse_search_page(page_html):
    """Return [{"asin", "title", "price"}] for the results of an Amazon search page."""
    results, seen = [], set()
    blocks = re.split(r'(?=<div[^>]*data-component-type="s-search-result")', page_html)[1:]
    for block in blocks:
        asin = re.search(r'data-asin="([A-Z0-9]{10})"', block)
        title = re.search(r'<h2[^>]*aria-label="([^"]+)"', block)
        if not asin or not title or asin.group(1) in seen:
            continue
        price = re.search(r'class="a-offscreen">\s*\$([\d,]+\.\d{2})', block)
        seen.add(asin.group(1))
        results.append({
            "asin": asin.group(1),
            "title": _clean(re.sub(r"^Sponsored Ad - ", "", html.unescape(title.group(1)))),
            "price": float(price.group(1).replace(",", "")) if price else None,
        })
    return results


def amazon_candidates(results):
    """Group qualifying search results by (item, condition), cheapest first."""
    groups, skipped = {}, []
    for result in results:
        config, reason = parse_config(result["title"])
        if config and config["ram"] not in RAM_LEVELS:
            continue
        if config and result["price"] is None:
            reason = "no price in search results"
        if reason:
            if LINE_RE.search(result["title"]):
                skipped.append({"listing": result["title"][:80], "reason": reason})
            continue
        groups.setdefault((item_name(config), config["condition"]), []).append(
            dict(result, config=config))
    for group in groups.values():
        group.sort(key=lambda r: r["price"])
    return groups, skipped


def amazon_row(page, candidate, run_date):
    """Return (row, None) when the product page confirms the candidate, else (None, reason)."""
    config, reason = parse_config(page["title"])
    if not config:
        return None, f"product page: {reason}"
    wanted = candidate["config"]
    if (item_name(config), config["condition"]) != (item_name(wanted), wanted["condition"]):
        return None, "product page shows a different configuration"
    if not page["price"]:
        return None, "no price"
    if not in_stock(page["availability"]):
        return None, f"not in stock ({page['availability'] or 'no stock message'})"
    seller = page["seller"].lower()
    store = "Amazon" if seller in ("", "amazon.com", "amazon") else "Amazon (third-party seller)"
    return make_row(config, store, config["condition"], page["price"],
                    PRODUCT_URL.format(asin=candidate["asin"]), run_date), None


def track_amazon(run_date, report, pause=2):
    results, seen = [], set()
    for ram in RAM_LEVELS:
        query = urllib.parse.quote_plus(AMAZON_QUERY.format(ram=ram))
        for _attempt in range(2):  # a captcha page comes back as 200 with no results
            status, body = fetch(AMAZON_SEARCH_URL.format(query=query))
            found = parse_search_page(body) if status == 200 else []
            if found:
                break
            time.sleep(pause)
        if not found:
            report["errors"].append(f"Amazon search for {ram}GB: no results "
                                    f"(status {status}; blocked or captcha)")
        results.extend(r for r in found if r["asin"] not in seen)
        seen.update(r["asin"] for r in found)
        time.sleep(pause)
    groups, skipped = amazon_candidates(results)
    report["skipped"].extend(skipped)
    rows = []
    for (item, _condition), candidates in sorted(groups.items()):
        for candidate in candidates[:AMAZON_TRIES]:
            status, body = fetch(PRODUCT_URL.format(asin=candidate["asin"]))
            time.sleep(pause)
            page = parse_product_page(body) if status == 200 else {"title": ""}
            if not page["title"]:
                report["errors"].append(f"{item}: no product page for {candidate['asin']} "
                                        f"(status {status}; blocked or captcha)")
                continue
            row, reason = amazon_row(page, candidate, run_date)
            if row:
                rows.append(row)
                break
            report["skipped"].append({"listing": f"{item} ({candidate['asin']})", "reason": reason})
    report["rows"].extend(cheapest_rows(rows))


SOURCES = {"apple": track_apple, "amazon": track_amazon}


def track(run_date, sources=tuple(SOURCES)):
    report = {"run_date": run_date, "rows": [], "skipped": [], "errors": []}
    for name in sources:
        SOURCES[name](run_date, report)
    return report


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--write", action="store_true", help="append qualifying rows to prices.csv")
    ap.add_argument("--source", choices=tuple(SOURCES), help="check only this source")
    ap.add_argument("--date", default=dt.date.today().isoformat(),
                    help="run date YYYY-MM-DD (default: today)")
    ap.add_argument("--csv", default=str(price_log.CSV_PATH), help="path to prices.csv")
    args = ap.parse_args(argv)

    price_log.parse_date(args.date)
    report = track(args.date, (args.source,) if args.source else tuple(SOURCES))

    print(f"\nMacBook price check for {report['run_date']} "
          f"(memory levels: {', '.join(f'{r}GB' for r in RAM_LEVELS)})")
    print("\nQualifying prices:")
    for r in report["rows"]:
        print(f"  {r['item']:<30} {r['spec']:<38} {r['store']:<30} {r['condition']:<12} "
              f"${float(r['price_usd']):>9,.2f}")
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
