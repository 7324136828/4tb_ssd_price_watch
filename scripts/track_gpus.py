#!/usr/bin/env python3
"""Track NVIDIA and AMD GPU prices and append verified rows to prices.csv.

Source: videocardprices.com card pages. Each page embeds the tracked Amazon
listing plus the cheapest Newegg (new) and eBay (used) listings it found, each
with a fetch timestamp, so every price comes with a date we can check.

Rules applied (see claude.md):
  * Only in-stock listings whose timestamp is within 2 days of the run date.
  * The listing title must be the exact model (an RX 9070 XT listing is never
    logged as an RX 9070).
  * eBay used listings are only reported, never written, because the script
    cannot check seller feedback or the return policy. Verify them by hand and
    log them with scripts/add_price.py.
  * Models the source does not cover (for example RTX 4090 / 3090) are listed
    in the report so they can be checked manually.

Usage:
    python scripts/track_gpus.py                 # dry run: print what would be logged
    python scripts/track_gpus.py --write         # append new rows to prices.csv
    python scripts/track_gpus.py --models "RTX 5090" "RX 9070 XT"
    python scripts/track_gpus.py --json report.json
"""
import argparse
import datetime as dt
import html
import json
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import price_log  # noqa: E402

BASE_URL = "https://videocardprices.com"
SOURCE_NAME = "videocardprices.com"
USER_AGENT = "Mozilla/5.0 (compatible; gpu-price-watch/1.0)"
TIMEOUT = 30

# Tracked models: category, card-page slugs to try (first hit wins), and a
# fallback spec used when the page does not list the memory.
TRACKED = {
    "RTX 5090": ("nvidia_gpu", ["nvidia-rtx-5090"], "32GB GDDR7"),
    "RTX 4090": ("nvidia_gpu", ["nvidia-rtx-4090"], "24GB GDDR6X"),
    "RTX 3090 Ti": ("nvidia_gpu", ["nvidia-rtx-3090-ti"], "24GB GDDR6X"),
    "RTX 3090": ("nvidia_gpu", ["nvidia-rtx-3090"], "24GB GDDR6X"),
    "RX 9070 XT": ("amd_gpu", ["amd-rx-9070-xt", "amd-radeon-rx-9070-xt"], "16GB GDDR6"),
    "RX 9070": ("amd_gpu", ["amd-rx-9070", "amd-radeon-rx-9070"], "16GB GDDR6"),
    "RX 7900 XTX": ("amd_gpu", ["amd-radeon-rx-7900-xtx", "amd-rx-7900-xtx"], "24GB GDDR6"),
    "RX 7900 XT": ("amd_gpu", ["amd-radeon-rx-7900-xt", "amd-rx-7900-xt"], "20GB GDDR6"),
}
# Any Radeon card on the source's home page numbered at or above this is
# tracked automatically ("any newer Radeon model positioned above the RX 9070 XT").
NEWER_RADEON_MIN = 9080

STORE_NAMES = {"amazon": "Amazon", "newegg": "Newegg", "ebay": "eBay",
               "bestbuy": "Best Buy", "walmart": "Walmart", "bhphoto": "B&H Photo",
               "microcenter": "Micro Center"}
NOT_WRITTEN_SOURCES = {"ebay"}  # seller feedback / returns cannot be verified here

MODEL_RE = re.compile(
    r"\b(RTX|RX)\s*-?\s*(\d{4})(?:\s*-?\s*(Ti\s*Super|Ti|Super|XTX|XT|GRE))?(?![A-Za-z])",
    re.IGNORECASE)
SUFFIX_CASE = {"ti super": "Ti Super", "ti": "Ti", "super": "Super",
               "xtx": "XTX", "xt": "XT", "gre": "GRE"}

# Words that end the "variant" part of a listing title, and words skipped in it.
VARIANT_STOP = {"graphics", "video", "card", "edition", "gpu", "dlss", "pci",
                "pcie", "express", "with", "for", "in", "-", "|"}
VARIANT_SKIP_RE = re.compile(
    r"^(\d+\s*g(b)?|gddr\w*|geforce|radeon|amd|nvidia|\d+-bit|pcie\S*)$", re.IGNORECASE)
VARIANT_MAX_WORDS = 3


# --------------------------------------------------------------------------- helpers
def normalize_model(text):
    """'GeForce RTX 3090 Ti 24GB' -> 'RTX 3090 Ti'; returns None when no model."""
    m = MODEL_RE.search(text or "")
    if not m:
        return None
    suffix = re.sub(r"\s+", " ", m.group(3) or "").lower()
    base = f"{m.group(1).upper()} {m.group(2)}"
    return f"{base} {SUFFIX_CASE[suffix]}" if suffix else base


def variant_name(title, brand=""):
    """Short board name from a listing title, e.g. 'ASUS TUF Gaming OC'."""
    title = re.split(r"[,(]", title or "", maxsplit=1)[0]
    m = MODEL_RE.search(title)
    if not m:
        return brand.strip()
    before = [w for w in title[:m.start()].split()
              if w.lower() not in ("geforce", "radeon", "amd", "nvidia")]
    after = []
    for word in title[m.end():].split():
        low = word.lower().strip(".,")
        if low in VARIANT_STOP or len(after) >= VARIANT_MAX_WORDS:
            break
        if VARIANT_SKIP_RE.match(low) or re.search(r"\d", word):
            continue  # memory size, part numbers like RX9070XT-16G
        if low in (w.lower() for w in before + after):
            continue
        after.append(word)
    words = before + after
    if brand and (not words or words[0].lower() != brand.lower()):
        words.insert(0, brand)
    return " ".join(words).strip()


def item_name(model, title, brand=""):
    variant = variant_name(title, brand)
    return f"{model} ({variant})" if variant else model


def spec_from_card(card, fallback):
    specs = card.get("specs") or {}
    memory = re.sub(r"\s+", "", str(specs.get("memory") or ""))
    mtype = str(specs.get("memoryType") or "").strip()
    if memory and mtype:
        return f"{memory} {mtype}"
    return fallback


def iso_date(timestamp):
    """'2026-11-14T14:38:23.02+00:00' or '...Z' -> '2026-11-14' (UTC)."""
    if not timestamp:
        return None
    ts = str(timestamp).strip().replace("Z", "+00:00")
    try:
        parsed = dt.datetime.fromisoformat(ts)
    except ValueError:
        try:
            return dt.date.fromisoformat(ts[:10]).isoformat()
        except ValueError:
            return None
    if parsed.tzinfo:
        parsed = parsed.astimezone(dt.timezone.utc)
    return parsed.date().isoformat()


def strip_query(url):
    return (url or "").split("?", 1)[0] if "amazon.com" in (url or "") else (url or "")


# --------------------------------------------------------------------------- parsing
def _devalue(x):
    """Decode Astro's island props encoding: [0, value] scalars/objects, [1, [...]] arrays."""
    if isinstance(x, list) and len(x) == 2 and isinstance(x[0], int):
        tag, value = x
        if tag == 1 and isinstance(value, list):
            return [_devalue(v) for v in value]
        return _devalue(value)
    if isinstance(x, dict):
        return {k: _devalue(v) for k, v in x.items()}
    return x


def parse_card_page(page_html):
    """Return the card dict embedded in a videocardprices.com card page, or None."""
    for m in re.finditer(r'<astro-island\b[^>]*?\sprops="([^"]*)"', page_html):
        try:
            props = json.loads(html.unescape(m.group(1)))
        except json.JSONDecodeError:
            continue
        if isinstance(props, dict) and "card" in props:
            card = _devalue(props["card"])
            if isinstance(card, dict) and "price" in card:
                return card
    return None


def discover_newer_radeons(home_html):
    """Card slugs for Radeon models numbered >= NEWER_RADEON_MIN found on the home page."""
    found = {}
    for slug in sorted(set(re.findall(r'href="/card/([a-z0-9-]+)/"', home_html))):
        if not slug.startswith("amd-"):
            continue
        model = normalize_model(slug.replace("-", " "))
        if model and model.startswith("RX ") and int(model.split()[1]) >= NEWER_RADEON_MIN:
            found.setdefault(model, slug)
    return found


def listings_from_card(card, model):
    """All listings on a card page as dicts with store/condition/price/title/url/date."""
    out = [{
        "source": "amazon",
        "condition": "new",
        "price": card.get("price"),
        "title": card.get("name", ""),
        "url": strip_query(card.get("amazonUrl") or ""),
        "date": iso_date(card.get("lastUpdated")),
        "in_stock": bool(card.get("inStock")),
        "brand": card.get("productBrand", ""),
    }]
    for p in card.get("prices") or []:
        out.append({
            "source": str(p.get("source", "")).lower(),
            "condition": str(p.get("condition", "")).lower(),
            "price": p.get("price"),
            "title": p.get("listingTitle", ""),
            "url": strip_query(p.get("url") or ""),
            "date": iso_date(p.get("fetchedAt")),
            "in_stock": bool(p.get("inStock")),
            "brand": "",  # third-party listing titles start with their own brand
        })
    return out


def evaluate(card, model, category, fallback_spec, run_date, page_url):
    """Split a card's listings into rows to write and skipped listings with reasons."""
    rows, skipped = [], []
    spec = spec_from_card(card, fallback_spec)
    for lst in listings_from_card(card, model):
        store = STORE_NAMES.get(lst["source"], lst["source"].title())
        label = f"{model} {store} {lst['condition']} ${lst['price']}"
        title_model = normalize_model(lst["title"]) or normalize_model(card.get("model"))
        reason = None
        if not isinstance(lst["price"], (int, float)) or lst["price"] <= 0:
            reason = "no price"
        elif title_model != model:
            reason = f"listing is a {title_model or 'different card'}, not {model}"
        elif not lst["in_stock"]:
            reason = "out of stock"
        elif not lst["date"]:
            reason = "listing has no date"
        elif not price_log.within_window(lst["date"], run_date):
            reason = f"price dated {lst['date']} is outside the {price_log.WINDOW_DAYS}-day window"
        elif lst["condition"] not in price_log.CONDITIONS:
            reason = f"unknown condition '{lst['condition']}'"
        elif store not in price_log.APPROVED_STORES:
            reason = f"{store} is not an approved store"
        elif lst["source"] in NOT_WRITTEN_SOURCES:
            reason = "eBay seller feedback/returns not verified (check by hand, log with add_price.py)"
        if reason:
            skipped.append({"listing": label, "title": lst["title"], "url": lst["url"],
                            "date": lst["date"], "reason": reason})
            continue
        rows.append({
            "date": run_date,
            "category": category,
            "item": item_name(model, lst["title"], lst["brand"]),
            "spec": spec,
            "store": store,
            "condition": lst["condition"],
            "price_usd": price_log.format_price(lst["price"]),
            "basis": f"reported ({SOURCE_NAME})",
            "source_date": lst["date"],
            "url": lst["url"] or page_url,
        })
    return rows, skipped


# --------------------------------------------------------------------------- fetching
def fetch(url, retries=3):
    """Return (status, body). status is the HTTP code, or 0 on a network error."""
    last = (0, "")
    for attempt in range(retries):
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT,
                                                   "Accept": "text/html"})
        try:
            with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
                return resp.status, resp.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            if e.code in (404, 410):
                return e.code, ""
            last = (e.code, "")
        except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
            last = (0, str(e))
        time.sleep(2 * (attempt + 1))
    return last


def track(models, run_date):
    report = {"run_date": run_date, "rows": [], "skipped": [], "no_source": [], "errors": []}
    targets = {m: TRACKED[m] for m in models}

    status, home = fetch(f"{BASE_URL}/")
    if status == 200:
        for model, slug in discover_newer_radeons(home).items():
            if model not in targets and model not in TRACKED:
                targets[model] = ("amd_gpu", [slug], "")
                print(f"Discovered newer Radeon model: {model}")
    else:
        report["errors"].append(f"home page fetch failed (status {status})")

    for model, (category, slugs, fallback_spec) in targets.items():
        card, page_url, statuses = None, None, []
        for slug in slugs:
            page_url = f"{BASE_URL}/card/{slug}/"
            status, body = fetch(page_url)
            statuses.append(status)
            if status == 200:
                card = parse_card_page(body)
                if card is None:
                    report["errors"].append(f"{model}: could not parse {page_url}")
                break
        if card is None:
            if all(s == 404 for s in statuses):
                report["no_source"].append(model)
            elif not any(model in e for e in report["errors"]):
                report["errors"].append(f"{model}: fetch failed (status {statuses})")
            continue
        rows, skipped = evaluate(card, model, category, fallback_spec, run_date, page_url)
        report["rows"].extend(rows)
        report["skipped"].extend(skipped)
    return report


# --------------------------------------------------------------------------- CLI
def print_report(report, added=None, dupes=None):
    print(f"\nGPU price check for {report['run_date']} (source: {SOURCE_NAME})")
    print("\nQualifying prices:")
    for r in report["rows"]:
        print(f"  {r['item']:<45} {r['store']:<8} {r['condition']:<5} "
              f"${float(r['price_usd']):>9,.2f}  (as of {r['source_date']})")
    if not report["rows"]:
        print("  none")
    if added is not None:
        print(f"\nWrote {len(added)} new row(s) to prices.csv; "
              f"{len(dupes)} already logged today.")
    if report["skipped"]:
        print("\nNot logged:")
        for s in report["skipped"]:
            print(f"  {s['listing']}: {s['reason']}")
    if report["no_source"]:
        print("\nNot covered by the source, check by hand: " + ", ".join(report["no_source"]))
    if report["errors"]:
        print("\nErrors:")
        for e in report["errors"]:
            print(f"  {e}")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--write", action="store_true", help="append qualifying rows to prices.csv")
    ap.add_argument("--date", default=dt.date.today().isoformat(),
                    help="run date YYYY-MM-DD (default: today)")
    ap.add_argument("--models", nargs="+", choices=sorted(TRACKED), default=list(TRACKED),
                    metavar="MODEL", help="models to check (default: all). "
                    f"Choices: {', '.join(TRACKED)}")
    ap.add_argument("--csv", default=str(price_log.CSV_PATH), help="path to prices.csv")
    ap.add_argument("--json", help="also write the full report to this JSON file")
    args = ap.parse_args(argv)

    price_log.parse_date(args.date)
    report = track(args.models, args.date)

    added = dupes = None
    if args.write:
        bad = [(r, p) for r in report["rows"] if (p := price_log.validate_row(r, args.date))]
        for r, p in bad:
            print(f"Refusing invalid row {r['item']}: {'; '.join(p)}", file=sys.stderr)
        added, dupes = price_log.append_rows(
            [r for r in report["rows"] if not price_log.validate_row(r, args.date)], args.csv)
    print_report(report, added, dupes)

    if args.json:
        Path(args.json).write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    # Exit 1 only when nothing at all could be fetched, so CI notices a broken source.
    fetched_any = report["rows"] or report["skipped"] or report["no_source"]
    return 0 if fetched_any else 1


if __name__ == "__main__":
    sys.exit(main())
