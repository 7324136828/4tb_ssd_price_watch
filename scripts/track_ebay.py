#!/usr/bin/env python3
"""Track eBay listings for SSDs, RAM modules and MacBooks and append rows to prices.csv.

Source: the official eBay Browse API (item_summary/search), a direct store
check. For every tracked item the script logs the cheapest qualifying New
listing and the cheapest qualifying Used/Refurbished listing.

The API needs a free eBay developer keyset (https://developer.ebay.com/).
Put the production App ID and Cert ID in these environment variables:

    EBAY_CLIENT_ID      App ID (Client ID)
    EBAY_CLIENT_SECRET  Cert ID (Client Secret)

Rules applied (see claude.md):
  * US listings, Buy It Now only (an auction's current bid is not a price),
    priced in USD. Search results only contain listings that can be bought now.
  * The title must name the exact product: the part number for RAM, the model
    and "4TB" for SSDs. Listings that also name another capacity (a
    multi-variation listing whose low price belongs to a smaller drive),
    heatsink / PS5 editions, kits, lots, empty boxes and for-parts items are
    skipped.
  * MacBooks: the title must name exactly one screen size, chip and memory
    size, and they must match the tracked configuration. Locked, damaged and
    parts listings are skipped. The storage in the title goes in spec.
  * A price below the item's floor (MIN_PRICE) is skipped as a likely scam or
    mislabeled listing rather than logged as a deal.
  * eBay condition "New" is logged as new, the refurbished grades as
    refurbished, and open box / used grades as used.

To track another product, add it to SSDS, RAM_MODULES or MACBOOKS.

Usage:
    python scripts/track_ebay.py                    # dry run: print what would be logged
    python scripts/track_ebay.py --write            # append new rows to prices.csv
    python scripts/track_ebay.py --category ram     # only RAM (or: ssd, macbook)
"""
import argparse
import base64
import datetime as dt
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import price_log  # noqa: E402
import track_macbooks  # noqa: E402

TOKEN_URL = "https://api.ebay.com/identity/v1/oauth2/token"
SEARCH_URL = "https://api.ebay.com/buy/browse/v1/item_summary/search"
SCOPE = "https://api.ebay.com/oauth/api_scope"
ITEM_URL = "https://www.ebay.com/itm/{item_id}"
TIMEOUT = 30
PAGE_SIZE = 50  # cheapest-first listings examined per item and condition group

# eBay conditionId -> prices.csv condition. 7000 ("for parts") is never logged.
CONDITION_BY_ID = {
    "1000": "new",
    "2000": "refurbished", "2010": "refurbished", "2020": "refurbished",
    "2030": "refurbished", "2500": "refurbished",
    "1500": "used", "1750": "used", "2750": "used", "3000": "used",
    "4000": "used", "5000": "used", "6000": "used",
}
# The two searches made per item: (label, conditionIds sent to the API).
CONDITION_GROUPS = (
    ("new", ("1000",)),
    ("used/refurbished", tuple(c for c in CONDITION_BY_ID if c != "1000")),
)

# Prices below these are treated as scams or mislabeled listings.
MIN_PRICE = {"ssd": 150.00, "ram": 250.00, "macbook": 900.00}

# item (as used in prices.csv), spec, search query, regex the title must match.
SSDS = [
    ("Lexar NM790", "4TB TLC", "Lexar NM790 4TB", r"\bNM790\b"),
    ("TeamGroup MP44", "4TB TLC", "TeamGroup MP44 4TB", r"\bMP44\b(?!\s*[A-Z])"),
    ("TeamGroup MP44Q", "4TB QLC", "TeamGroup MP44Q 4TB", r"\bMP44Q\b"),
    ("TeamGroup T-Force G50", "4TB TLC", "T-Force G50 4TB", r"\bG50\b(?!\s*EVO)"),
    ("WD Black SN7100", "4TB TLC", "SN7100 4TB", r"\bSN7100\b|\bGX\s*7100\b"),
    ("WD Black SN850X", "4TB TLC", "SN850X 4TB", r"\bSN850X\b|\b850X\b"),
    ("WD Blue SN5000", "4TB QLC", "WD Blue SN5000 4TB", r"\bSN5000\b"),
    ("WD Blue SN5100", "4TB QLC", "SN5100 4TB", r"\bSN5100\b|\bOptimus\s*5100\b"),
    ("Samsung 990 EVO Plus", "4TB TLC", "Samsung 990 EVO Plus 4TB", r"\b990\s*EVO\s*Plus\b"),
    ("Samsung 990 Pro", "4TB TLC", "Samsung 990 Pro 4TB", r"\b990\s*PRO\b"),
    ("Crucial T500", "4TB TLC", "Crucial T500 4TB", r"\bT500\b"),
    ("Crucial P310", "4TB QLC", "Crucial P310 4TB", r"\bP310\b"),
    ("Kingston KC3000", "4TB TLC", "Kingston KC3000 4TB", r"\bKC3000\b"),
    ("Silicon Power UD90", "4TB TLC (some batches reported QLC)", "Silicon Power UD90 4TB",
     r"\bUD90\b"),
]
# item, spec, part number (searched for, and required in the title).
RAM_MODULES = [
    ("Crucial CT64G56C46S5", "1x64GB DDR5-5600 CL46", "CT64G56C46S5"),
    ("G.Skill F5-5600S4645A64GX1-RS", "1x64GB DDR5-5600 CL46", "F5-5600S4645A64GX1-RS"),
]

# MacBook configurations: (screen sizes, chip, memory levels in GB). Each
# combination is one tracked item, named like scripts/track_macbooks.py names it.
MACBOOKS = [
    ((14, 16), "M1 Max", (64,)),
    ((14, 16), "M2 Max", (64, 96)),
    ((14, 16), "M3 Max", (64, 96, 128)),
    ((14, 16), "M4 Max", (64, 128)),
    ((14, 16), "M5 Max", (64, 128)),
]
MACBOOK_REJECT_RE = re.compile(
    r"\b(icloud|activation lock|mdm|locked|cracked|damaged?|no power|water|"
    r"bad (battery|screen|display)|missing)\b", re.IGNORECASE)

JUNK_RE = re.compile(
    r"\b(for parts|not working|broken|faulty|untested|as[- ]is|read (the )?description|"
    r"empty box|box only|no (ssd|drive)|lot of|bulk lot|\d+\s*(pcs|pack|lot)\b|"
    r"enclosure|adapter|caddy)", re.IGNORECASE)
SSD_REJECT_RE = re.compile(r"\b(heat\s*-?\s*sink|heat\s*spreader|PS5|external|portable)\b",
                           re.IGNORECASE)
RAM_REJECT_RE = re.compile(
    r"(\b\d\s*x\s*\d+\s*GB\b|\b\d+\s*GB\s*x\s*[2-9]\b|\(\s*[2-9]\s*x|\bkit\b|\bpair\b|"
    r"\b128\s*GB\b|\bECC\b|\bregistered\b|\bRDIMM\b|\bUDIMM\b)", re.IGNORECASE)
CAPACITY_RE = re.compile(r"(?<![\d.])(\d+(?:\.\d+)?)\s*(TB|GB)\b", re.IGNORECASE)


def targets(category=None):
    """Tracked products as dicts: category, item, spec, query, title_re.

    MacBook targets have no fixed spec or title_re; reject_reason and to_row
    read the configuration from each listing title instead.
    """
    out = []
    if category in (None, "ssd"):
        for item, spec, query, pattern in SSDS:
            out.append({"category": "ssd", "item": item, "spec": spec, "query": query,
                        "title_re": re.compile(pattern, re.IGNORECASE)})
    if category in (None, "ram"):
        for item, spec, part in RAM_MODULES:
            out.append({"category": "ram", "item": item, "spec": spec, "query": part,
                        "title_re": re.compile(re.escape(part), re.IGNORECASE)})
    if category in (None, "macbook"):
        for sizes, chip, levels in MACBOOKS:
            for size in sizes:
                for ram in levels:
                    item = f"MacBook Pro {size} {chip} {ram}GB"
                    out.append({"category": "macbook", "item": item,
                                "query": f"MacBook Pro {size} {chip} {ram}GB"})
    return out


def reject_reason(target, listing):
    """Why this API listing must not be logged for target, or None when it qualifies."""
    title = listing.get("title", "")
    price = listing.get("price") or {}
    if price.get("currency") != "USD":
        return "not priced in USD"
    try:
        value = float(price.get("value"))
    except (TypeError, ValueError):
        return "no price"
    if "FIXED_PRICE" not in listing.get("buyingOptions", ["FIXED_PRICE"]):
        return "auction only"
    if (listing.get("itemLocation") or {}).get("country", "US") != "US":
        return "not a US listing"
    if str(listing.get("conditionId", "")) not in CONDITION_BY_ID:
        return f"condition not logged ({listing.get('condition') or 'unknown'})"
    if target["category"] == "macbook":
        config, reason = track_macbooks.parse_config(title)
        if not config:
            return reason
        if track_macbooks.item_name(config) != target["item"]:
            return "title names a different configuration"
    elif not target["title_re"].search(title):
        return "title does not name the product"
    if JUNK_RE.search(title):
        return "parts, lot, empty box or accessory listing"
    if target["category"] == "macbook":
        if MACBOOK_REJECT_RE.search(title):
            return "locked or damaged listing"
    elif target["category"] == "ssd":
        sizes = {f"{float(n):g}{u.upper()}" for n, u in CAPACITY_RE.findall(title)}
        if "4TB" not in sizes:
            return "title does not say 4TB"
        if sizes - {"4TB"}:
            return "title names more than one capacity"
        if SSD_REJECT_RE.search(title):
            return "heatsink, PS5 or external drive"
    else:
        if RAM_REJECT_RE.search(title):
            return "kit, multi-module or ECC listing"
    if value < MIN_PRICE[target["category"]]:
        return f"price ${value:,.2f} is below the ${MIN_PRICE[target['category']]:,.2f} floor"
    return None


def to_row(target, listing, run_date):
    item_id = listing.get("legacyItemId") or str(listing.get("itemId", "")).split("|")[1]
    spec = target.get("spec")
    if target["category"] == "macbook":
        spec = track_macbooks.spec_text(track_macbooks.parse_config(listing["title"])[0])
    return {
        "date": run_date, "category": target["category"], "item": target["item"],
        "spec": spec, "store": "eBay",
        "condition": CONDITION_BY_ID[str(listing["conditionId"])],
        "price_usd": price_log.format_price(listing["price"]["value"]),
        "basis": "direct", "source_date": run_date,
        "url": ITEM_URL.format(item_id=item_id),
    }


def cheapest(target, listings, run_date):
    """Return (row or None, skipped) for one condition group's listings."""
    skipped, best = [], None
    for lst in listings:
        reason = reject_reason(target, lst)
        if reason:
            skipped.append({"listing": f"{target['item']}: {lst.get('title', '')[:70]}",
                            "reason": reason})
        elif best is None or float(lst["price"]["value"]) < float(best["price"]["value"]):
            best = lst
    return (to_row(target, best, run_date) if best else None), skipped


def _request(url, headers, data=None):
    req = urllib.request.Request(url, headers=headers, data=data)
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        return json.loads(resp.read().decode("utf-8"))


def get_token(client_id, client_secret, request=_request):
    basic = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
    body = urllib.parse.urlencode({"grant_type": "client_credentials", "scope": SCOPE}).encode()
    reply = request(TOKEN_URL, {"Authorization": f"Basic {basic}",
                                "Content-Type": "application/x-www-form-urlencoded"}, body)
    return reply["access_token"]


def search(token, query, condition_ids, request=_request):
    """Cheapest-first US Buy It Now listings for query in the given conditions."""
    params = {
        "q": query, "sort": "price", "limit": PAGE_SIZE,
        "filter": ("buyingOptions:{FIXED_PRICE},itemLocationCountry:US,priceCurrency:USD,"
                   f"conditionIds:{{{'|'.join(condition_ids)}}}"),
    }
    reply = request(f"{SEARCH_URL}?{urllib.parse.urlencode(params)}",
                    {"Authorization": f"Bearer {token}",
                     "X-EBAY-C-MARKETPLACE-ID": "EBAY_US", "Accept": "application/json"})
    return reply.get("itemSummaries", [])


def track(run_date, token, category=None, request=_request, pause=0.5):
    report = {"run_date": run_date, "rows": [], "skipped": [], "errors": []}
    for target in targets(category):
        for label, condition_ids in CONDITION_GROUPS:
            try:
                listings = search(token, target["query"], condition_ids, request)
            except (urllib.error.URLError, TimeoutError, ConnectionError, ValueError) as e:
                report["errors"].append(f"{target['item']} ({label}): search failed ({e})")
                continue
            row, skipped = cheapest(target, listings, run_date)
            report["skipped"].extend(skipped)
            if row:
                report["rows"].append(row)
            time.sleep(pause)
    return report


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--write", action="store_true", help="append qualifying rows to prices.csv")
    ap.add_argument("--category", choices=("ssd", "ram", "macbook"), help="check only this category")
    ap.add_argument("--date", default=dt.date.today().isoformat(),
                    help="run date YYYY-MM-DD (default: today)")
    ap.add_argument("--csv", default=str(price_log.CSV_PATH), help="path to prices.csv")
    ap.add_argument("--verbose", action="store_true", help="also list every skipped listing")
    args = ap.parse_args(argv)
    price_log.parse_date(args.date)

    client_id = os.environ.get("EBAY_CLIENT_ID")
    client_secret = os.environ.get("EBAY_CLIENT_SECRET")
    if not (client_id and client_secret):
        print("error: set EBAY_CLIENT_ID and EBAY_CLIENT_SECRET (eBay developer keyset) "
              "to use the eBay Browse API.", file=sys.stderr)
        return 2
    try:
        token = get_token(client_id, client_secret)
    except (urllib.error.URLError, TimeoutError, ConnectionError, ValueError, KeyError) as e:
        print(f"error: could not get an eBay API token ({e}). eBay may be blocking this "
              "network, or the keyset is wrong.", file=sys.stderr)
        return 1

    report = track(args.date, token, args.category)
    print(f"\neBay price check for {report['run_date']} (source: eBay Browse API)")
    print("\nQualifying prices:")
    for r in report["rows"]:
        print(f"  {r['category']:<7} {r['item']:<32} {r['condition']:<12} "
              f"${float(r['price_usd']):>9,.2f}  {r['url']}")
    if not report["rows"]:
        print("  none")
    if args.write:
        rows = [r for r in report["rows"] if not price_log.validate_row(r, args.date)]
        added, dupes = price_log.append_rows(rows, args.csv)
        print(f"\nWrote {len(added)} new row(s) to prices.csv; {len(dupes)} already logged today.")
    print(f"\n{len(report['skipped'])} listing(s) skipped by the title, condition and price rules.")
    if args.verbose:
        for s in report["skipped"]:
            print(f"  {s['listing']}: {s['reason']}")
    if report["errors"]:
        print("\nErrors:")
        for e in report["errors"]:
            print(f"  {e}")
    return 1 if report["errors"] and not report["rows"] else 0


if __name__ == "__main__":
    sys.exit(main())
