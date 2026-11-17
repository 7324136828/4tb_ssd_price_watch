#!/usr/bin/env python3
"""Visualize price changes over time from prices.csv.

Generates a self-contained interactive HTML dashboard (zero external assets,
uses only the Python standard library) and opens it in your default browser,
while also printing a concise price-change summary in the terminal.

Usage:
    python3 scripts/visualize_prices.py
    python3 scripts/visualize_prices.py --category ssd
    python3 scripts/visualize_prices.py --metric pct --no-open
    python3 scripts/visualize_prices.py --terminal
"""
import argparse
import csv
import datetime as dt
import html
import json
import math
import sys
import tempfile
import webbrowser
from collections import defaultdict
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
ROOT = SCRIPTS_DIR.parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import build_readme  # noqa: E402

DEFAULT_CSV = ROOT / "prices.csv"
DEFAULT_OUTPUT = Path(tempfile.gettempdir()) / "4tb_ssd_price_watch_dashboard.html"

PALETTE = [
    "#2563eb",  # blue
    "#dc2626",  # red
    "#059669",  # emerald
    "#d97706",  # amber
    "#7c3aed",  # violet
    "#0891b2",  # cyan
    "#db2777",  # pink
    "#4f46e5",  # indigo
    "#65a30d",  # lime
    "#ea580c",  # orange
    "#0d9488",  # teal
    "#9333ea",  # purple
]

SPARK_CHARS = "▁▂▃▄▅▆▇█"


def parse_price(raw):
    """Parse a positive finite USD price string, returning float or None."""
    if raw is None:
        return None
    cleaned = str(raw).strip().replace("$", "").replace(",", "")
    if not cleaned:
        return None
    try:
        val = float(cleaned)
    except ValueError:
        return None
    if not math.isfinite(val) or val < 0:
        return None
    return val


def parse_iso_date(raw):
    """Parse an ISO YYYY-MM-DD date string, returning datetime.date or None."""
    text = (raw or "").strip()
    if not text:
        return None
    try:
        return dt.date.fromisoformat(text)
    except ValueError:
        return None


def load_rows(csv_path):
    """Load and validate rows from a prices CSV file."""
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")

    rows = []
    skipped = 0
    with csv_path.open(newline="", encoding="utf-8-sig") as f:
        for raw in csv.DictReader(f):
            price = parse_price(raw.get("price_usd"))
            date_obj = parse_iso_date(raw.get("date"))
            if price is None or date_obj is None:
                skipped += 1
                continue
            row = {
                "price": price,
                "date": date_obj.isoformat(),
                "_date_obj": date_obj,
            }
            for key in ("category", "item", "spec", "store", "condition", "basis", "source_date", "url"):
                row[key] = (raw.get(key) or "").strip()
            row["category"] = row["category"].lower() or "other"
            row["condition"] = row["condition"].lower() or "new"
            if row["source_date"] and parse_iso_date(row["source_date"]) is None:
                row["source_date"] = ""
            rows.append(row)
    return rows, skipped


def enrich_rows(rows):
    """Compute per-series historical changes, deal flags, and metadata."""
    if not rows:
        return []

    all_days = sorted({r["date"] for r in rows})
    day_counts = {d: sum(1 for x in all_days if x <= d) for d in all_days}

    # Index earlier prices by (category, item, condition) for all-time-low checks.
    by_item_cond = defaultdict(list)
    for r in rows:
        by_item_cond[(r["category"], r["item"], r["condition"])].append((r["date"], r["price"], id(r)))

    grouped = defaultdict(list)
    for r in rows:
        grouped[build_readme.series_key(r)].append(r)

    enriched = []
    for key, hist in grouped.items():
        hist.sort(key=lambda r: r["date"])
        first_price = hist[0]["price"]

        same_day_totals = defaultdict(int)
        for r in hist:
            same_day_totals[r["date"]] += 1
        same_day_seen = defaultdict(int)

        for idx, cur in enumerate(hist):
            prev = hist[idx - 1] if idx > 0 else None
            change_prev = None if prev is None else cur["price"] - prev["price"]
            pct_prev = None if (prev is None or prev["price"] == 0) else (change_prev / prev["price"]) * 100.0
            change_first = cur["price"] - first_price
            pct_first = 0.0 if first_price == 0 else (change_first / first_price) * 100.0

            earlier = [
                p for d, p, rid in by_item_cond[(cur["category"], cur["item"], cur["condition"])]
                if rid != id(cur) and d < cur["date"]
            ]
            deals = build_readme.deal_reasons(cur, prev, earlier, day_counts[cur["date"]])

            d_str = cur["date"]
            sd_idx = same_day_seen[d_str]
            same_day_seen[d_str] += 1

            cat = cur["category"]
            enriched.append({
                **cur,
                "series_key": key,
                "change_prev": change_prev,
                "pct_prev": pct_prev,
                "change_first": change_first,
                "pct_first": pct_first,
                "deals": deals,
                "same_day_index": sd_idx,
                "same_day_total": same_day_totals[d_str],
                "gpu_model": build_readme.gpu_model(cur) if cat in build_readme.GPU_MODELS else "",
                "is_tlc": build_readme.is_tlc(cur["spec"]),
                "capacity_tb": build_readme.capacity_tb(cur["spec"]),
                "is_4tb_ssd": build_readme.is_4tb_ssd(cur),
            })
    return enriched


def filter_rows(rows, args):
    """Apply optional CLI filters to enriched rows."""
    since_d = parse_iso_date(args.since) if args.since else None
    until_d = parse_iso_date(args.until) if args.until else None
    if args.since and since_d is None:
        raise ValueError(f"Invalid --since date (expected YYYY-MM-DD): {args.since}")
    if args.until and until_d is None:
        raise ValueError(f"Invalid --until date (expected YYYY-MM-DD): {args.until}")

    cat_filter = args.category.strip().lower() if args.category else "all"
    cond_filter = args.condition.strip().lower() if args.condition else "all"
    item_q = args.item.strip().lower() if args.item else ""
    store_q = args.store.strip().lower() if args.store else ""

    out = []
    for r in rows:
        if cat_filter != "all" and r["category"] != cat_filter:
            continue
        if cond_filter == "new" and r["condition"] != "new":
            continue
        if cond_filter == "used" and r["condition"] == "new":
            continue
        if item_q and item_q not in r["item"].lower() and item_q not in r["spec"].lower():
            continue
        if store_q and store_q not in r["store"].lower():
            continue
        if since_d and r["_date_obj"] < since_d:
            continue
        if until_d and r["_date_obj"] > until_d:
            continue
        out.append(r)
    return out


def build_series_payload(rows):
    """Group enriched rows into JSON-serializable series sorted consistently."""
    grouped = defaultdict(list)
    for r in rows:
        grouped[r["series_key"]].append(r)

    cats = build_readme.category_order(rows)
    cat_rank = {c: i for i, c in enumerate(cats)}

    def sort_key(item_pair):
        key, pts = item_pair
        cat, item, store, cond = key
        latest_price = pts[-1]["price"]
        return (cat_rank.get(cat, 999), latest_price, item.lower(), store.lower(), cond.lower())

    ordered = sorted(grouped.items(), key=sort_key)
    cat_color_idx = defaultdict(int)
    series_list = []
    for idx, (key, pts) in enumerate(ordered):
        cat, item, store, cond = key
        pts.sort(key=lambda p: (p["date"], p["same_day_index"]))
        color = PALETTE[cat_color_idx[cat] % len(PALETTE)]
        cat_color_idx[cat] += 1

        sample = pts[-1]
        series_list.append({
            "id": f"s{idx}",
            "category": cat,
            "categoryLabel": build_readme.cat_names(cat)[0],
            "item": item,
            "spec": sample["spec"],
            "store": store,
            "condition": cond,
            "gpuModel": sample["gpu_model"],
            "isTlc": any(p["is_tlc"] for p in pts),
            "is4tbSsd": any(p["is_4tb_ssd"] for p in pts),
            "capacityTb": max(p["capacity_tb"] for p in pts),
            "color": color,
            "points": [
                {
                    "date": p["date"],
                    "sourceDate": p["source_date"],
                    "price": round(p["price"], 2),
                    "changePrev": None if p["change_prev"] is None else round(p["change_prev"], 2),
                    "pctPrev": None if p["pct_prev"] is None else round(p["pct_prev"], 2),
                    "changeFirst": round(p["change_first"], 2),
                    "pctFirst": round(p["pct_first"], 2),
                    "basis": p["basis"],
                    "url": p["url"],
                    "deals": p["deals"],
                    "sameDayIndex": p["same_day_index"],
                    "sameDayTotal": p["same_day_total"],
                }
                for p in pts
            ],
        })
    return cats, series_list


def sparkline(values):
    """Render a compact Unicode sparkline for a sequence of numeric prices."""
    if len(values) < 2:
        return "·"
    lo, hi = min(values), max(values)
    if math.isclose(lo, hi):
        return SPARK_CHARS[len(SPARK_CHARS) // 2] * len(values)
    span = hi - lo
    return "".join(
        SPARK_CHARS[min(len(SPARK_CHARS) - 1, max(0, int((v - lo) / span * (len(SPARK_CHARS) - 1))))]
        for v in values
    )


def format_delta(delta, pct):
    if delta is None:
        return "new"
    if abs(delta) < 0.005:
        return "0.00 (0.0%)"
    sign = "+" if delta > 0 else "-"
    return f"{sign}${abs(delta):,.2f} ({sign}{abs(pct):.1f}%)"


def render_ascii_chart(title, points_by_series, width=68, height=12):
    """Render a simple ASCII/Unicode multi-series price-vs-time plot for terminal mode."""
    all_pts = [(d, p) for _, pts in points_by_series for d, p in pts]
    if not all_pts:
        return ""

    dates = sorted({d for d, _ in all_pts})
    prices = [p for _, p in all_pts]
    lo, hi = min(prices), max(prices)
    if math.isclose(lo, hi):
        lo = max(0.0, lo - 10.0)
        hi = hi + 10.0
    else:
        pad = (hi - lo) * 0.1
        lo = max(0.0, lo - pad)
        hi = hi + pad

    grid = [[" " for _ in range(width)] for _ in range(height)]
    symbols = "*+ox#@%&"

    date_objs = [dt.date.fromisoformat(d) for d in dates]
    min_ord = date_objs[0].toordinal()
    max_ord = date_objs[-1].toordinal()
    span_ord = max(1, max_ord - min_ord)

    def to_xy(date_str, price):
        ord_d = dt.date.fromisoformat(date_str).toordinal()
        if len(dates) == 1:
            x = width // 2
        else:
            x = int(round((ord_d - min_ord) / span_ord * (width - 1)))
        y = int(round((hi - price) / (hi - lo) * (height - 1)))
        return max(0, min(width - 1, x)), max(0, min(height - 1, y))

    legend = []
    for s_idx, (label, pts) in enumerate(points_by_series):
        sym = symbols[s_idx % len(symbols)]
        legend.append(f"{sym} {label}")
        coords = [to_xy(d, p) for d, p in pts]
        for i in range(len(coords) - 1):
            x0, y0 = coords[i]
            x1, y1 = coords[i + 1]
            steps = max(abs(x1 - x0), abs(y1 - y0), 1)
            for step in range(1, steps):
                xi = int(round(x0 + (x1 - x0) * step / steps))
                yi = int(round(y0 + (y1 - y0) * step / steps))
                if grid[yi][xi] == " ":
                    grid[yi][xi] = "·"
        for x, y in coords:
            grid[y][x] = sym

    lines = [f"  {title}"]
    fmt_y = ",.2f" if (hi - lo) < 20 else ",.0f"
    for r in range(height):
        val = hi - (hi - lo) * r / max(1, height - 1)
        y_str = f"${val:{fmt_y}}"
        label_str = f"{y_str:>9} │" if r in (0, height // 2, height - 1) else "          │"
        lines.append(label_str + "".join(grid[r]))
    lines.append("          └" + "─" * width)
    if len(dates) == 1:
        pad_left = width // 2 - len(dates[0]) // 2
        lines.append("           " + " " * max(0, pad_left) + dates[0])
    else:
        left, right = dates[0], dates[-1]
        gap = max(1, width - len(left) - len(right))
        lines.append("           " + left + " " * gap + right)
    lines.append("  Legend: " + "  |  ".join(legend))
    return "\n".join(lines)


def print_terminal_summary(rows, series_list, cats, csv_path, show_charts=False):
    """Print a structured summary of prices and changes over time to stdout."""
    print(f"Nitro V 16S Upgrade Price Watch — {csv_path}")
    if not rows:
        print("No matching price observations found.")
        return

    dates = sorted({r["date"] for r in rows})
    span_days = (dt.date.fromisoformat(dates[-1]) - dt.date.fromisoformat(dates[0])).days + 1
    print(
        f"Observations: {len(rows)} | Series: {len(series_list)} | "
        f"Dates: {dates[0]} to {dates[-1]} ({len(dates)} logged day{'s' if len(dates) != 1 else ''}, "
        f"{span_days}-day span)"
    )

    by_cat = defaultdict(list)
    for s in series_list:
        by_cat[s["category"]].append(s)

    for cat in cats:
        cat_name = build_readme.cat_names(cat)[0]
        print(f"\n[{cat_name}]")
        header = (
            f"  {'Item':<30} {'Store':<12} {'Cond':<6} {'Latest':>10}  "
            f"{'vs Prev':<18} {'vs 1st':<18} {'Range (Low-High)':<21} {'Pts':>3}  Trend"
        )
        print(header)
        print("  " + "-" * (len(header) - 2))
        for s in by_cat[cat]:
            pts = s["points"]
            prices = [p["price"] for p in pts]
            cur = pts[-1]
            item_disp = s["item"][:28] + ".." if len(s["item"]) > 30 else s["item"]
            store_disp = s["store"][:10] + ".." if len(s["store"]) > 12 else s["store"]
            latest_str = f"${cur['price']:,.2f}"
            prev_str = format_delta(cur["changePrev"], cur["pctPrev"])
            first_str = (
                "baseline"
                if (len(pts) == 1 and cur["changePrev"] is None)
                else format_delta(cur["changeFirst"], cur["pctFirst"])
            )
            rng = f"${min(prices):,.2f}-${max(prices):,.2f}"
            deal_mark = " 🔥" if cur["deals"] else ""
            print(
                f"  {item_disp:<30} {store_disp:<12} {s['condition']:<6} "
                f"{latest_str:>10}  {prev_str:<18} {first_str:<18} "
                f"{rng:<21} {len(pts):>3}  {sparkline(prices)}{deal_mark}"
            )

        if show_charts:
            chart_series = [
                (f"{s['item']} ({s['store']})", [(p["date"], p["price"]) for p in s["points"]])
                for s in by_cat[cat]
            ]
            print()
            print(render_ascii_chart(f"{cat_name} — Price vs Time (USD)", chart_series))


HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__PAGE_TITLE__</title>
<style>
  :root {
    --bg: #f6f8fb;
    --surface: #ffffff;
    --surface-2: #f0f4f9;
    --border: #dce3ed;
    --text: #0f172a;
    --muted: #526075;
    --accent: #2563eb;
    --accent-soft: rgba(37, 99, 235, 0.12);
    --good: #059669;
    --good-soft: rgba(5, 150, 105, 0.12);
    --bad: #dc2626;
    --bad-soft: rgba(220, 38, 38, 0.12);
    --warn: #d97706;
    --warn-soft: rgba(217, 119, 6, 0.13);
    --grid: #e5ebf3;
    --tooltip-bg: rgba(15, 23, 42, 0.96);
    --tooltip-text: #f8fafc;
    --shadow: 0 4px 18px rgba(15, 23, 42, 0.06);
  }
  [data-theme="dark"] {
    --bg: #0b1120;
    --surface: #111827;
    --surface-2: #1a2436;
    --border: #273449;
    --text: #f1f5f9;
    --muted: #94a3b8;
    --accent: #60a5fa;
    --accent-soft: rgba(96, 165, 250, 0.16);
    --good: #34d399;
    --good-soft: rgba(52, 211, 153, 0.14);
    --bad: #f87171;
    --bad-soft: rgba(248, 113, 113, 0.14);
    --warn: #fbbf24;
    --warn-soft: rgba(251, 191, 36, 0.16);
    --grid: #1f2b3d;
    --tooltip-bg: rgba(2, 6, 23, 0.96);
    --tooltip-text: #f8fafc;
    --shadow: 0 6px 24px rgba(0, 0, 0, 0.35);
  }
  * { box-sizing: border-box; }
  body {
    margin: 0;
    background: var(--bg);
    color: var(--text);
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Inter, Roboto, Helvetica, Arial, sans-serif;
    line-height: 1.45;
  }
  .container {
    max-width: 1380px;
    margin: 0 auto;
    padding: 20px 22px 48px;
  }
  header {
    display: flex;
    flex-wrap: wrap;
    justify-content: space-between;
    align-items: flex-start;
    gap: 16px;
    margin-bottom: 18px;
  }
  h1 {
    margin: 0 0 4px;
    font-size: 1.45rem;
    font-weight: 700;
    letter-spacing: -0.02em;
  }
  .subtitle {
    color: var(--muted);
    font-size: 0.88rem;
  }
  .header-actions {
    display: flex;
    gap: 8px;
    align-items: center;
  }
  button, select, input {
    font: inherit;
    color: var(--text);
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 6px 11px;
    font-size: 0.85rem;
  }
  button {
    cursor: pointer;
    transition: background 0.15s ease, border-color 0.15s ease;
  }
  button:hover { background: var(--surface-2); }
  button.active {
    background: var(--accent);
    color: #ffffff;
    border-color: var(--accent);
    font-weight: 600;
  }
  .kpi-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
    gap: 12px;
    margin-bottom: 16px;
  }
  .kpi-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 12px 14px;
    box-shadow: var(--shadow);
  }
  .kpi-label {
    font-size: 0.74rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: var(--muted);
    font-weight: 600;
  }
  .kpi-value {
    margin-top: 4px;
    font-size: 1.25rem;
    font-weight: 700;
    font-variant-numeric: tabular-nums;
  }
  .kpi-sub {
    margin-top: 2px;
    font-size: 0.8rem;
    color: var(--muted);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  .tabs {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin-bottom: 12px;
  }
  .tab-btn {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 7px 13px;
    border-radius: 999px;
    font-weight: 500;
  }
  .tab-count {
    font-size: 0.75rem;
    padding: 1px 6px;
    border-radius: 999px;
    background: var(--surface-2);
    color: var(--muted);
  }
  .tab-btn.active .tab-count {
    background: rgba(255,255,255,0.22);
    color: #fff;
  }
  .controls {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 12px 14px;
    margin-bottom: 16px;
    box-shadow: var(--shadow);
    display: flex;
    flex-wrap: wrap;
    gap: 10px 14px;
    align-items: center;
  }
  .ctrl-group {
    display: inline-flex;
    align-items: center;
    gap: 6px;
  }
  .ctrl-label {
    font-size: 0.78rem;
    color: var(--muted);
    font-weight: 600;
  }
  .seg-group {
    display: inline-flex;
    border: 1px solid var(--border);
    border-radius: 8px;
    overflow: hidden;
  }
  .seg-group button {
    border: none;
    border-radius: 0;
    border-right: 1px solid var(--border);
    padding: 5px 10px;
    font-size: 0.82rem;
  }
  .seg-group button:last-child { border-right: none; }
  .check-label {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    font-size: 0.82rem;
    color: var(--text);
    cursor: pointer;
    user-select: none;
  }
  .check-label input { width: auto; padding: 0; margin: 0; }
  .banner {
    background: var(--accent-soft);
    border: 1px solid rgba(37, 99, 235, 0.25);
    color: var(--text);
    border-radius: 10px;
    padding: 9px 14px;
    font-size: 0.84rem;
    margin-bottom: 14px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 12px;
    flex-wrap: wrap;
  }
  .charts-grid {
    display: grid;
    grid-template-columns: 1fr;
    gap: 16px;
    margin-bottom: 18px;
  }
  .charts-grid.multi {
    grid-template-columns: repeat(auto-fit, minmax(560px, 1fr));
  }
  @media (max-width: 640px) {
    .charts-grid.multi { grid-template-columns: 1fr; }
  }
  .chart-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 14px 16px 12px;
    box-shadow: var(--shadow);
    position: relative;
  }
  .chart-header {
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    gap: 10px;
    margin-bottom: 8px;
    flex-wrap: wrap;
  }
  .chart-title {
    font-size: 1.02rem;
    font-weight: 700;
  }
  .chart-meta {
    font-size: 0.8rem;
    color: var(--muted);
  }
  .svg-wrap {
    width: 100%;
    position: relative;
  }
  svg.price-svg {
    width: 100%;
    display: block;
    overflow: visible;
    user-select: none;
  }
  .legend {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    margin-top: 10px;
    padding-top: 10px;
    border-top: 1px solid var(--border);
  }
  .legend-item {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 4px 9px;
    border-radius: 999px;
    border: 1px solid var(--border);
    background: var(--surface-2);
    font-size: 0.79rem;
    cursor: pointer;
    transition: opacity 0.15s ease, border-color 0.15s ease;
  }
  .legend-item.hidden {
    opacity: 0.42;
    text-decoration: line-through;
  }
  .legend-item.focused {
    border-color: var(--accent);
    box-shadow: 0 0 0 2px var(--accent-soft);
  }
  .swatch {
    width: 10px;
    height: 10px;
    border-radius: 50%;
    flex-shrink: 0;
  }
  .swatch.dashed {
    border-radius: 2px;
    background: transparent !important;
    border: 2px solid;
  }
  .inspector {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 11px 14px;
    margin-bottom: 18px;
    box-shadow: var(--shadow);
    display: flex;
    flex-wrap: wrap;
    justify-content: space-between;
    align-items: center;
    gap: 10px;
    font-size: 0.86rem;
  }
  .inspector a {
    color: var(--accent);
    font-weight: 600;
    text-decoration: none;
  }
  .inspector a:hover { text-decoration: underline; }
  .panel {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 14px 16px;
    box-shadow: var(--shadow);
    margin-bottom: 16px;
  }
  .panel-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 10px;
    gap: 10px;
    flex-wrap: wrap;
  }
  .panel-title {
    font-size: 0.98rem;
    font-weight: 700;
  }
  .table-wrap {
    overflow-x: auto;
  }
  table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.84rem;
    font-variant-numeric: tabular-nums;
  }
  th, td {
    text-align: left;
    padding: 8px 10px;
    border-bottom: 1px solid var(--border);
    white-space: nowrap;
  }
  th {
    color: var(--muted);
    font-weight: 600;
    font-size: 0.77rem;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    cursor: pointer;
    user-select: none;
  }
  th:hover { color: var(--text); }
  th.num, td.num { text-align: right; }
  tbody tr { cursor: pointer; }
  tbody tr:hover { background: var(--surface-2); }
  tbody tr.selected-row { background: var(--accent-soft); }
  .pill {
    display: inline-block;
    padding: 2px 7px;
    border-radius: 999px;
    font-size: 0.75rem;
    font-weight: 600;
  }
  .pill-good { background: var(--good-soft); color: var(--good); }
  .pill-bad { background: var(--bad-soft); color: var(--bad); }
  .pill-neutral { background: var(--surface-2); color: var(--muted); }
  .pill-deal { background: var(--warn-soft); color: var(--warn); }
  .tooltip {
    position: fixed;
    z-index: 1000;
    pointer-events: none;
    background: var(--tooltip-bg);
    color: var(--tooltip-text);
    border-radius: 10px;
    padding: 10px 12px;
    font-size: 0.8rem;
    line-height: 1.45;
    box-shadow: 0 12px 32px rgba(0,0,0,0.32);
    max-width: 340px;
    opacity: 0;
    transition: opacity 0.08s ease;
  }
  .tooltip.visible { opacity: 1; }
  .tooltip-title { font-weight: 700; font-size: 0.86rem; margin-bottom: 3px; }
  .tooltip-row { display: flex; justify-content: space-between; gap: 14px; }
  .tooltip-muted { color: #cbd5e1; font-size: 0.76rem; }
  .empty-state {
    text-align: center;
    padding: 48px 20px;
    color: var(--muted);
    background: var(--surface);
    border: 1px dashed var(--border);
    border-radius: 14px;
  }
  a.ext-link {
    color: var(--accent);
    text-decoration: none;
    font-weight: 500;
  }
  a.ext-link:hover { text-decoration: underline; }
</style>
</head>
<body>
<div class="container">
  <header>
    <div>
      <h1>Nitro V 16S Upgrade Price Watch</h1>
      <div class="subtitle" id="subtitle">Loading price history...</div>
    </div>
    <div class="header-actions">
      <button id="resetFocusBtn" type="button" style="display:none;">Show All Series</button>
      <button id="exportSvgBtn" type="button">Export SVG</button>
      <button id="themeBtn" type="button">Dark Mode</button>
    </div>
  </header>

  <div class="kpi-grid" id="kpiGrid"></div>
  <div class="tabs" id="categoryTabs"></div>

  <div class="controls" id="controlsBar">
    <div class="ctrl-group">
      <span class="ctrl-label">View</span>
      <div class="seg-group" id="metricGroup">
        <button type="button" data-metric="price">Price ($)</button>
        <button type="button" data-metric="pct">% Change</button>
        <button type="button" data-metric="envelope">Daily Cheapest</button>
      </div>
    </div>

    <div class="ctrl-group" id="scaleCtrl">
      <span class="ctrl-label">Scale</span>
      <div class="seg-group" id="scaleGroup">
        <button type="button" data-scale="linear">Linear</button>
        <button type="button" data-scale="log">Log</button>
      </div>
    </div>

    <div class="ctrl-group">
      <span class="ctrl-label">Date</span>
      <div class="seg-group" id="dateFieldGroup">
        <button type="button" data-datefield="date">Log Date</button>
        <button type="button" data-datefield="sourceDate">Source Date</button>
      </div>
    </div>

    <div class="ctrl-group">
      <span class="ctrl-label">Range</span>
      <div class="seg-group" id="rangeGroup">
        <button type="button" data-range="all">All</button>
        <button type="button" data-range="7">7D</button>
        <button type="button" data-range="30">30D</button>
        <button type="button" data-range="90">90D</button>
      </div>
    </div>

    <div class="ctrl-group">
      <span class="ctrl-label">Condition</span>
      <select id="condSelect">
        <option value="all">All</option>
        <option value="new">New only</option>
        <option value="used">Used / Refurb</option>
      </select>
    </div>

    <div class="ctrl-group">
      <span class="ctrl-label">Store</span>
      <select id="storeSelect"><option value="all">All stores</option></select>
    </div>

    <div class="ctrl-group" id="gpuModelCtrl" style="display:none;">
      <span class="ctrl-label">GPU Model</span>
      <select id="gpuModelSelect"><option value="all">All models</option></select>
    </div>

    <div class="ctrl-group" id="ssdFilterCtrl" style="display:none;">
      <span class="ctrl-label">SSD Filter</span>
      <select id="ssdFilterSelect">
        <option value="all">All SSDs</option>
        <option value="4tb">4TB+ only</option>
        <option value="tlc">TLC only</option>
        <option value="qlc">QLC only</option>
      </select>
    </div>

    <div class="ctrl-group">
      <input id="searchInput" type="search" placeholder="Filter item or spec..." style="width:185px;">
    </div>

    <label class="check-label"><input type="checkbox" id="dealLineCheck" checked> $450 SSD target</label>
    <label class="check-label"><input type="checkbox" id="maCheck"> 7-day avg</label>
    <label class="check-label"><input type="checkbox" id="labelsCheck" checked> Point labels</label>
  </div>

  <div id="bannerSlot"></div>
  <div class="charts-grid" id="chartsGrid"></div>
  <div class="inspector" id="inspectorBar" style="display:none;"></div>

  <div class="panel">
    <div class="panel-header">
      <div class="panel-title">Tracked Series Summary (Click a row to highlight)</div>
      <div class="chart-meta" id="tableCount"></div>
    </div>
    <div class="table-wrap">
      <table id="seriesTable">
        <thead>
          <tr>
            <th data-sort="category">Category</th>
            <th data-sort="item">Item</th>
            <th data-sort="spec">Spec</th>
            <th data-sort="store">Store</th>
            <th data-sort="condition">Cond</th>
            <th data-sort="latest" class="num">Latest</th>
            <th data-sort="changePrev" class="num">vs Prev</th>
            <th data-sort="pctFirst" class="num">vs 1st</th>
            <th data-sort="min" class="num">Low</th>
            <th data-sort="max" class="num">High</th>
            <th data-sort="count" class="num">Entries</th>
            <th data-sort="latestDate">As Of</th>
            <th>Source</th>
          </tr>
        </thead>
        <tbody id="seriesTableBody"></tbody>
      </table>
    </div>
  </div>

  <div class="panel">
    <div class="panel-header">
      <div class="panel-title">Chronological Price Observations (Newest First)</div>
      <div class="chart-meta" id="logCount"></div>
    </div>
    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Date</th>
            <th>Category</th>
            <th>Item</th>
            <th>Store</th>
            <th>Cond</th>
            <th class="num">Price</th>
            <th class="num">Change vs Prev</th>
            <th>Basis</th>
            <th>Source Date</th>
            <th>Link</th>
          </tr>
        </thead>
        <tbody id="obsTableBody"></tbody>
      </table>
    </div>
  </div>
</div>

<div class="tooltip" id="tooltip"></div>
<script id="price-payload" type="application/json">__PAYLOAD_JSON__</script>
<script>
(function () {
  "use strict";

  const payload = JSON.parse(document.getElementById("price-payload").textContent);
  const META = payload.meta;
  const ALL_SERIES = payload.series;

  const state = {
    category: META.initial.category || "all",
    metric: META.initial.metric || "price",
    scale: "linear",
    dateField: "date",
    rangeDays: "all",
    condition: "all",
    store: "all",
    gpuModel: "all",
    ssdFilter: "all",
    search: "",
    showDealLine: true,
    showMa: false,
    showLabels: true,
    hiddenIds: new Set(),
    focusedId: null,
    selectedPoint: null,
    sortKey: "latest",
    sortAsc: true,
  };

  function escapeHtml(str) {
    return String(str == null ? "" : str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  function safeUrl(url) {
    const s = String(url || "").trim();
    return /^https?:\/\//i.test(s) ? s : "";
  }

  function fmtMoney(v) {
    if (v == null || !isFinite(v)) return "—";
    return "$" + Number(v).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  }

  function fmtSignedMoney(v) {
    if (v == null || !isFinite(v)) return "—";
    if (Math.abs(v) < 0.005) return "$0.00";
    return (v > 0 ? "+" : "-") + fmtMoney(Math.abs(v));
  }

  function fmtSignedPct(v) {
    if (v == null || !isFinite(v)) return "—";
    if (Math.abs(v) < 0.05) return "0.0%";
    return (v > 0 ? "+" : "-") + Math.abs(v).toFixed(1) + "%";
  }

  function parseDayMs(iso) {
    if (!iso) return NaN;
    const parts = iso.split("-").map(Number);
    if (parts.length !== 3) return NaN;
    return Date.UTC(parts[0], parts[1] - 1, parts[2]);
  }

  function fmtShortDate(ms) {
    const d = new Date(ms);
    const y = d.getUTCFullYear();
    const m = String(d.getUTCMonth() + 1).padStart(2, "0");
    const day = String(d.getUTCDate()).padStart(2, "0");
    return `${y}-${m}-${day}`;
  }

  function fmtAxisDate(ms, spanDays) {
    const d = new Date(ms);
    const months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
    const label = `${months[d.getUTCMonth()]} ${d.getUTCDate()}`;
    return spanDays > 250 ? `${label} '${String(d.getUTCFullYear()).slice(-2)}` : label;
  }

  function niceTicks(minVal, maxVal, targetCount) {
    if (!isFinite(minVal) || !isFinite(maxVal)) return [0, 1];
    if (minVal === maxVal) {
      const pad = Math.max(10, Math.abs(minVal) * 0.1);
      minVal -= pad;
      maxVal += pad;
    }
    const range = maxVal - minVal;
    const roughStep = range / Math.max(2, targetCount - 1);
    const pow10 = Math.pow(10, Math.floor(Math.log10(roughStep)));
    const frac = roughStep / pow10;
    let niceFrac = 1;
    if (frac <= 1.2) niceFrac = 1;
    else if (frac <= 2.2) niceFrac = 2;
    else if (frac <= 3.2) niceFrac = 2.5;
    else if (frac <= 5.5) niceFrac = 5;
    else niceFrac = 10;
    const step = niceFrac * pow10;
    const start = Math.floor(minVal / step) * step;
    const end = Math.ceil(maxVal / step) * step;
    const ticks = [];
    for (let v = start; v <= end + step * 0.001; v += step) {
      ticks.push(Number(v.toPrecision(10)));
    }
    return ticks;
  }

  function applyTheme(theme) {
    document.documentElement.setAttribute("data-theme", theme);
    document.getElementById("themeBtn").textContent = theme === "dark" ? "Light Mode" : "Dark Mode";
    try { localStorage.setItem("pw_theme", theme); } catch (_) {}
  }

  (function initTheme() {
    let saved = null;
    try { saved = localStorage.getItem("pw_theme"); } catch (_) {}
    if (!saved && window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches) {
      saved = "dark";
    }
    applyTheme(saved === "dark" ? "dark" : "light");
  })();

  function populateDropdowns() {
    const storeSel = document.getElementById("storeSelect");
    const stores = Array.from(new Set(ALL_SERIES.map(s => s.store).filter(Boolean))).sort();
    stores.forEach(st => {
      const opt = document.createElement("option");
      opt.value = st;
      opt.textContent = st;
      storeSel.appendChild(opt);
    });

    const gpuSel = document.getElementById("gpuModelSelect");
    const gpuModels = Array.from(new Set(ALL_SERIES.map(s => s.gpuModel).filter(Boolean)));
    gpuModels.forEach(m => {
      const opt = document.createElement("option");
      opt.value = m;
      opt.textContent = m;
      gpuSel.appendChild(opt);
    });
  }

  function pointDateStr(pt) {
    if (state.dateField === "sourceDate" && pt.sourceDate) return pt.sourceDate;
    return pt.date;
  }

  function getMaxDateMs() {
    let maxMs = -Infinity;
    for (const s of ALL_SERIES) {
      for (const p of s.points) {
        const ms = parseDayMs(pointDateStr(p));
        if (isFinite(ms) && ms > maxMs) maxMs = ms;
      }
    }
    return maxMs;
  }

  function getFilteredSeries() {
    const q = state.search.trim().toLowerCase();
    const maxMs = getMaxDateMs();
    const cutoffMs = state.rangeDays === "all" || !isFinite(maxMs)
      ? -Infinity
      : maxMs - (Number(state.rangeDays) - 1) * 86400000;

    const result = [];
    for (const s of ALL_SERIES) {
      if (state.category !== "all" && s.category !== state.category) continue;
      if (state.condition === "new" && s.condition !== "new") continue;
      if (state.condition === "used" && s.condition === "new") continue;
      if (state.store !== "all" && s.store !== state.store) continue;
      if (state.gpuModel !== "all" && s.gpuModel !== state.gpuModel) continue;
      if (s.category === "ssd") {
        if (state.ssdFilter === "4tb" && !s.is4tbSsd) continue;
        if (state.ssdFilter === "tlc" && !s.isTlc) continue;
        if (state.ssdFilter === "qlc" && !/\bqlc\b/i.test(s.spec)) continue;
      }
      if (q && !(s.item.toLowerCase().includes(q) || s.spec.toLowerCase().includes(q) || s.store.toLowerCase().includes(q))) {
        continue;
      }

      const pts = [];
      for (const p of s.points) {
        const dStr = pointDateStr(p);
        const ms = parseDayMs(dStr);
        if (!isFinite(ms) || ms < cutoffMs) continue;
        const intraOffset = p.sameDayTotal > 1 ? (p.sameDayIndex / p.sameDayTotal) * 0.35 * 86400000 : 0;
        pts.push({
          ...p,
          activeDate: dStr,
          xMs: ms + intraOffset,
          dayMs: ms,
        });
      }
      if (!pts.length) continue;

      const basePrice = pts[0].price;
      const rebasedPts = pts.map((p, idx) => {
        const prev = idx > 0 ? pts[idx - 1] : null;
        const cFirst = p.price - basePrice;
        const pFirst = basePrice === 0 ? 0 : (cFirst / basePrice) * 100;
        const cPrev = prev ? p.price - prev.price : p.changePrev;
        const pPrev = prev && prev.price ? ((p.price - prev.price) / prev.price) * 100 : p.pctPrev;
        return {
          ...p,
          viewChangeFirst: cFirst,
          viewPctFirst: pFirst,
          viewChangePrev: cPrev,
          viewPctPrev: pPrev,
        };
      });
      result.push({ ...s, viewPoints: rebasedPts });
    }
    return result;
  }

  function buildEnvelopeSeries(filtered) {
    // Group by category (or GPU model / SSD tier), computing cheapest price per day.
    const groups = new Map();
    for (const s of filtered) {
      let groupKey = s.category;
      let groupLabel = `${s.categoryLabel}: Cheapest`;
      if (s.category === "ssd") {
        if (s.is4tbSsd) {
          groupKey = s.isTlc ? "ssd_4tb_tlc" : "ssd_4tb_any";
          groupLabel = s.isTlc ? "SSDs: Cheapest 4TB TLC" : "SSDs: Cheapest 4TB (Other/QLC)";
        } else {
          groupKey = "ssd_other";
          groupLabel = "SSDs: Cheapest (Other / 2TB)";
        }
      } else if (s.gpuModel) {
        groupKey = `${s.category}::${s.gpuModel}`;
        groupLabel = `${s.gpuModel}: Cheapest`;
      }
      if (!groups.has(groupKey)) {
        groups.set(groupKey, {
          id: "env_" + groupKey,
          category: s.category,
          categoryLabel: s.categoryLabel,
          item: groupLabel,
          spec: "Daily minimum across filtered stores",
          store: "Best store",
          condition: state.condition === "used" ? "used" : "all",
          gpuModel: s.gpuModel,
          isTlc: s.isTlc,
          is4tbSsd: s.is4tbSsd,
          color: s.color,
          byDay: new Map(),
        });
      }
      const g = groups.get(groupKey);
      for (const p of s.viewPoints) {
        const cur = g.byDay.get(p.activeDate);
        if (!cur || p.price < cur.price) {
          g.byDay.set(p.activeDate, { ...p, sourceItem: s.item, sourceStore: s.store, sourceSpec: s.spec });
        }
      }
    }

    const out = [];
    let colorIdx = 0;
    for (const g of groups.values()) {
      const days = Array.from(g.byDay.keys()).sort();
      const rawPts = days.map(d => g.byDay.get(d));
      const base = rawPts[0].price;
      const viewPoints = rawPts.map((p, idx) => {
        const prev = idx > 0 ? rawPts[idx - 1] : null;
        return {
          ...p,
          xMs: p.dayMs,
          viewChangeFirst: p.price - base,
          viewPctFirst: base === 0 ? 0 : ((p.price - base) / base) * 100,
          viewChangePrev: prev ? p.price - prev.price : null,
          viewPctPrev: prev && prev.price ? ((p.price - prev.price) / prev.price) * 100 : null,
          basis: `${p.sourceItem} @ ${p.sourceStore} (${p.basis})`,
        };
      });
      out.push({
        ...g,
        color: PALETTE[colorIdx++ % PALETTE.length],
        viewPoints,
      });
    }
    return out;
  }

  function isSeriesVisible(s) {
    if (state.focusedId && s.id !== state.focusedId) return false;
    return !state.hiddenIds.has(s.id);
  }

  function renderTabs(filteredBeforeCategory) {
    const el = document.getElementById("categoryTabs");
    const counts = new Map();
    for (const s of ALL_SERIES) {
      counts.set(s.category, (counts.get(s.category) || 0) + 1);
    }

    const tabs = [{ key: "all", label: "All Categories", count: ALL_SERIES.length }];
    for (const cat of META.categoryOrder) {
      const lbl = (META.categories[cat] && META.categories[cat][0]) || cat;
      tabs.push({ key: cat, label: lbl, count: counts.get(cat) || 0 });
    }

    el.innerHTML = tabs.map(t => {
      const active = state.category === t.key ? "active" : "";
      return `<button type="button" class="tab-btn ${active}" data-cat="${escapeHtml(t.key)}">` +
        `${escapeHtml(t.label)} <span class="tab-count">${t.count}</span></button>`;
    }).join("");

    el.querySelectorAll("button").forEach(btn => {
      btn.addEventListener("click", () => {
        state.category = btn.dataset.cat;
        state.focusedId = null;
        state.selectedPoint = null;
        render();
      });
    });
  }

  function renderKpis(filtered) {
    const el = document.getElementById("kpiGrid");
    const allPts = filtered.flatMap(s => s.viewPoints.map(p => ({ series: s, pt: p })));
    const uniqueDates = Array.from(new Set(allPts.map(x => x.pt.activeDate))).sort();

    if (!allPts.length) {
      el.innerHTML = `<div class="kpi-card"><div class="kpi-label">Observations</div><div class="kpi-value">0</div><div class="kpi-sub">Adjust filters to see data</div></div>`;
      return;
    }

    const cheapestEntry = allPts.reduce((best, cur) => (cur.pt.price < best.pt.price ? cur : best), allPts[0]);
    const latestDate = uniqueDates[uniqueDates.length - 1];
    const latestNew = allPts.filter(x => x.pt.activeDate === latestDate && x.series.condition === "new");
    const bestLatest = (latestNew.length ? latestNew : allPts.filter(x => x.pt.activeDate === latestDate))
      .reduce((best, cur) => (cur.pt.price < best.pt.price ? cur : best));

    const multiPtSeries = filtered.filter(s => s.viewPoints.length >= 2);
    let biggestDrop = null;
    let biggestGain = null;
    for (const s of multiPtSeries) {
      const last = s.viewPoints[s.viewPoints.length - 1];
      if (biggestDrop === null || last.viewPctFirst < biggestDrop.pct) {
        biggestDrop = { series: s, pct: last.viewPctFirst, delta: last.viewChangeFirst };
      }
      if (biggestGain === null || last.viewPctFirst > biggestGain.pct) {
        biggestGain = { series: s, pct: last.viewPctFirst, delta: last.viewChangeFirst };
      }
    }

    const activeDeals = filtered.filter(s => s.viewPoints[s.viewPoints.length - 1].deals.length > 0);
    const spanText = uniqueDates.length === 1
      ? `${uniqueDates[0]} (1 logged day)`
      : `${uniqueDates[0]} → ${uniqueDates[uniqueDates.length - 1]} (${uniqueDates.length} days)`;

    el.innerHTML = `
      <div class="kpi-card">
        <div class="kpi-label">Tracked Scope</div>
        <div class="kpi-value">${filtered.length} series · ${allPts.length} pts</div>
        <div class="kpi-sub">${escapeHtml(spanText)}</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">Cheapest on ${escapeHtml(latestDate)}</div>
        <div class="kpi-value">${fmtMoney(bestLatest.pt.price)}</div>
        <div class="kpi-sub">${escapeHtml(bestLatest.series.item)} (${escapeHtml(bestLatest.series.store)})</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">Biggest Drop (Period)</div>
        <div class="kpi-value" style="color:${biggestDrop && biggestDrop.delta < 0 ? 'var(--good)' : 'var(--text)'}">
          ${biggestDrop ? fmtSignedPct(biggestDrop.pct) : "—"}
        </div>
        <div class="kpi-sub">${biggestDrop ? escapeHtml(`${biggestDrop.series.item} (${fmtSignedMoney(biggestDrop.delta)})`) : "Needs 2+ dates per series"}</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">Biggest Increase / Lowest Ever</div>
        <div class="kpi-value" style="color:${biggestGain && biggestGain.delta > 0 ? 'var(--bad)' : 'var(--text)'}">
          ${biggestGain ? fmtSignedPct(biggestGain.pct) : fmtMoney(cheapestEntry.pt.price)}
        </div>
        <div class="kpi-sub">${biggestGain ? escapeHtml(`${biggestGain.series.item} (${fmtSignedMoney(biggestGain.delta)})`) : escapeHtml(`All-time low: ${cheapestEntry.series.item}`)}</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">Active DEAL Flags 🔥</div>
        <div class="kpi-value" style="color:${activeDeals.length ? 'var(--warn)' : 'var(--text)'}">${activeDeals.length}</div>
        <div class="kpi-sub">${activeDeals.length ? escapeHtml(activeDeals.map(d => d.item).join(", ")) : "Target: 4TB TLC ≤ " + fmtMoney(META.dealPriceSsd)}</div>
      </div>
    `;
  }

  function updateControlVisibility(filtered) {
    const hasGpu = state.category === "nvidia_gpu" || state.category === "amd_gpu" ||
      (state.category === "all" && ALL_SERIES.some(s => Boolean(s.gpuModel)));
    const hasSsd = state.category === "ssd" || (state.category === "all" && ALL_SERIES.some(s => s.category === "ssd"));

    document.getElementById("gpuModelCtrl").style.display = hasGpu ? "inline-flex" : "none";
    document.getElementById("ssdFilterCtrl").style.display = hasSsd ? "inline-flex" : "none";
    document.getElementById("scaleCtrl").style.display = state.metric === "pct" ? "none" : "inline-flex";
    document.getElementById("resetFocusBtn").style.display =
      (state.focusedId || state.hiddenIds.size > 0) ? "inline-block" : "none";

    document.querySelectorAll("#metricGroup button").forEach(b => {
      b.classList.toggle("active", b.dataset.metric === state.metric);
    });
    document.querySelectorAll("#scaleGroup button").forEach(b => {
      b.classList.toggle("active", b.dataset.scale === state.scale);
    });
    document.querySelectorAll("#dateFieldGroup button").forEach(b => {
      b.classList.toggle("active", b.dataset.datefield === state.dateField);
    });
    document.querySelectorAll("#rangeGroup button").forEach(b => {
      b.classList.toggle("active", b.dataset.range === state.rangeDays);
    });
  }

  function movingAveragePoints(pts, windowDays) {
    if (pts.length < 2) return [];
    const msWindow = windowDays * 86400000;
    return pts.map(p => {
      const nearby = pts.filter(q => q.xMs <= p.xMs && q.xMs > p.xMs - msWindow);
      const avg = nearby.reduce((sum, q) => sum + q.yVal, 0) / nearby.length;
      return { xMs: p.xMs, yVal: avg };
    });
  }

  function layoutPointLabels(labelNodes, topY, bottomY) {
    labelNodes.sort((a, b) => a.y - b.y);
    const minGap = 15;
    for (let i = 1; i < labelNodes.length; i++) {
      if (labelNodes[i].labelY - labelNodes[i - 1].labelY < minGap) {
        labelNodes[i].labelY = labelNodes[i - 1].labelY + minGap;
      }
    }
    if (labelNodes.length && labelNodes[labelNodes.length - 1].labelY > bottomY - 4) {
      let overflow = labelNodes[labelNodes.length - 1].labelY - (bottomY - 4);
      labelNodes[labelNodes.length - 1].labelY -= overflow;
      for (let i = labelNodes.length - 2; i >= 0; i--) {
        if (labelNodes[i + 1].labelY - labelNodes[i].labelY < minGap) {
          labelNodes[i].labelY = labelNodes[i + 1].labelY - minGap;
        }
      }
    }
    for (const node of labelNodes) {
      node.labelY = Math.max(topY + 10, Math.min(bottomY - 4, node.labelY));
    }
  }

  function showTooltip(evt, item) {
    const tip = document.getElementById("tooltip");
    const pt = item.pt;
    const s = item.series;
    const dealsHtml = pt.deals && pt.deals.length
      ? `<div style="margin-top:4px;color:#fbbf24;font-weight:600;">🔥 DEAL: ${escapeHtml(pt.deals.join(", "))}</div>`
      : "";
    const sameDayTag = pt.sameDayTotal > 1 ? ` (entry ${pt.sameDayIndex + 1}/${pt.sameDayTotal})` : "";

    tip.innerHTML = `
      <div class="tooltip-title">${escapeHtml(s.item)}</div>
      <div class="tooltip-muted" style="margin-bottom:5px;">${escapeHtml(s.spec || s.categoryLabel)}</div>
      <div class="tooltip-row"><span>Price</span><strong>${fmtMoney(pt.price)}</strong></div>
      <div class="tooltip-row"><span>Store / Cond</span><span>${escapeHtml(s.store)} · ${escapeHtml(s.condition)}</span></div>
      <div class="tooltip-row"><span>Date</span><span>${escapeHtml(pt.activeDate)}${escapeHtml(sameDayTag)}</span></div>
      ${pt.sourceDate ? `<div class="tooltip-row"><span>Source Date</span><span>${escapeHtml(pt.sourceDate)}</span></div>` : ""}
      <div class="tooltip-row"><span>vs Previous</span><span>${pt.viewChangePrev == null ? "first entry" : `${fmtSignedMoney(pt.viewChangePrev)} (${fmtSignedPct(pt.viewPctPrev)})`}</span></div>
      <div class="tooltip-row"><span>vs First</span><span>${fmtSignedMoney(pt.viewChangeFirst)} (${fmtSignedPct(pt.viewPctFirst)})</span></div>
      ${pt.basis ? `<div class="tooltip-muted" style="margin-top:4px;">Basis: ${escapeHtml(pt.basis)}</div>` : ""}
      ${dealsHtml}
    `;
    tip.classList.add("visible");

    const pad = 14;
    const rect = tip.getBoundingClientRect();
    let left = evt.clientX + 16;
    let top = evt.clientY - rect.height / 2;
    if (left + rect.width + pad > window.innerWidth) left = evt.clientX - rect.width - 16;
    if (top < pad) top = pad;
    if (top + rect.height + pad > window.innerHeight) top = window.innerHeight - rect.height - pad;
    tip.style.left = left + "px";
    tip.style.top = top + "px";
  }

  function hideTooltip() {
    document.getElementById("tooltip").classList.remove("visible");
  }

  function updateInspector(series, pt) {
    const bar = document.getElementById("inspectorBar");
    if (!series || !pt) {
      bar.style.display = "none";
      return;
    }
    const href = safeUrl(pt.url);
    const linkHtml = href ? `<a href="${escapeHtml(href)}" target="_blank" rel="noopener noreferrer">Open source listing ↗</a>` : "";
    const dealHtml = pt.deals && pt.deals.length
      ? ` <span class="pill pill-deal">🔥 ${escapeHtml(pt.deals.join(", "))}</span>`
      : "";
    bar.style.display = "flex";
    bar.innerHTML = `
      <div>
        <strong>${escapeHtml(series.item)}</strong>
        <span style="color:var(--muted);">(${escapeHtml(series.store)}, ${escapeHtml(series.condition)})</span>
        — <strong>${fmtMoney(pt.price)}</strong> on ${escapeHtml(pt.activeDate)}
        · vs prev: ${pt.viewChangePrev == null ? "first entry" : `${fmtSignedMoney(pt.viewChangePrev)} (${fmtSignedPct(pt.viewPctPrev)})`}
        · vs 1st: ${fmtSignedMoney(pt.viewChangeFirst)} (${fmtSignedPct(pt.viewPctFirst)})
        ${dealHtml}
      </div>
      <div>${linkHtml}</div>
    `;
  }

  function renderChartCard(container, title, subtitle, seriesList, options) {
    const card = document.createElement("div");
    card.className = "chart-card";

    const header = document.createElement("div");
    header.className = "chart-header";
    header.innerHTML = `
      <div class="chart-title">${escapeHtml(title)}</div>
      <div class="chart-meta">${escapeHtml(subtitle)}</div>
    `;
    card.appendChild(header);

    const svgWrap = document.createElement("div");
    svgWrap.className = "svg-wrap";
    card.appendChild(svgWrap);

    const legend = document.createElement("div");
    legend.className = "legend";
    seriesList.forEach(s => {
      const last = s.viewPoints[s.viewPoints.length - 1];
      const item = document.createElement("button");
      item.type = "button";
      item.className = "legend-item" +
        (state.hiddenIds.has(s.id) ? " hidden" : "") +
        (state.focusedId === s.id ? " focused" : "");
      item.title = "Click to toggle visibility · Double-click to isolate";
      const pctBadge = s.viewPoints.length > 1
        ? ` (${fmtSignedPct(last.viewPctFirst)})`
        : "";
      const swatchClass = s.condition !== "new" ? "swatch dashed" : "swatch";
      const swatchStyle = s.condition !== "new"
        ? `border-color:${s.color};`
        : `background:${s.color};`;
      item.innerHTML = `<span class="${swatchClass}" style="${swatchStyle}"></span>` +
        `<span>${escapeHtml(s.item)} · ${escapeHtml(s.store)}</span>` +
        `<strong>${fmtMoney(last.price)}${escapeHtml(pctBadge)}</strong>`;
      item.addEventListener("click", () => {
        if (state.focusedId === s.id) {
          state.focusedId = null;
        } else if (state.hiddenIds.has(s.id)) {
          state.hiddenIds.delete(s.id);
        } else {
          state.hiddenIds.add(s.id);
        }
        render();
      });
      item.addEventListener("dblclick", e => {
        e.preventDefault();
        state.focusedId = state.focusedId === s.id ? null : s.id;
        state.hiddenIds.delete(s.id);
        render();
      });
      legend.appendChild(item);
    });
    card.appendChild(legend);
    container.appendChild(card);

    function drawSvg() {
      const visible = seriesList.filter(isSeriesVisible);
      const width = Math.max(360, Math.floor(svgWrap.clientWidth || 720));
      const height = options.compact ? 300 : 410;
      const margin = { top: 20, right: 28, bottom: 42, left: 74 };
      const plotW = width - margin.left - margin.right;
      const plotH = height - margin.top - margin.bottom;

      if (!visible.length) {
        svgWrap.innerHTML = `<div class="empty-state" style="padding:36px;">All series hidden — click legend items below to show them.</div>`;
        return;
      }

      const isPct = state.metric === "pct";
      const useLog = !isPct && state.scale === "log";

      const plotted = visible.map(s => ({
        series: s,
        pts: s.viewPoints.map(p => ({
          ...p,
          yVal: isPct ? p.viewPctFirst : p.price,
        })).filter(p => !useLog || p.yVal > 0),
      })).filter(s => s.pts.length > 0);

      if (!plotted.length) {
        svgWrap.innerHTML = `<div class="empty-state" style="padding:36px;">No positive prices to plot on log scale.</div>`;
        return;
      }

      const allPts = plotted.flatMap(g => g.pts.map(p => ({ series: g.series, pt: p })));
      let minX = Math.min(...allPts.map(a => a.pt.xMs));
      let maxX = Math.max(...allPts.map(a => a.pt.xMs));
      const singleDay = (maxX - minX) < 86400000 * 0.5;
      if (singleDay) {
        minX -= 2 * 86400000;
        maxX += 2 * 86400000;
      } else {
        const padX = Math.max(86400000 * 0.4, (maxX - minX) * 0.04);
        minX -= padX;
        maxX += padX;
      }

      let rawYVals = allPts.map(a => a.pt.yVal);
      const showDealTarget = !isPct && state.showDealLine &&
        plotted.some(g => g.series.category === "ssd");
      if (showDealTarget) rawYVals.push(META.dealPriceSsd);
      if (isPct) rawYVals.push(0);

      let yTicks, yMin, yMax, yToPx;
      if (useLog) {
        const minLog = Math.log10(Math.max(1, Math.min(...rawYVals) * 0.9));
        const maxLog = Math.log10(Math.max(...rawYVals) * 1.1);
        const spanLog = Math.max(0.1, maxLog - minLog);
        yMin = Math.pow(10, minLog);
        yMax = Math.pow(10, maxLog);
        yTicks = [];
        const pStart = Math.floor(minLog);
        const pEnd = Math.ceil(maxLog);
        for (let p = pStart; p <= pEnd; p++) {
          for (const mult of [1, 2, 5]) {
            const val = mult * Math.pow(10, p);
            if (val >= yMin * 0.98 && val <= yMax * 1.02) yTicks.push(val);
          }
        }
        if (yTicks.length < 3) yTicks = [yMin, (yMin + yMax) / 2, yMax];
        yToPx = val => margin.top + (1 - (Math.log10(Math.max(1e-6, val)) - minLog) / spanLog) * plotH;
      } else {
        const lo = Math.min(...rawYVals);
        const hi = Math.max(...rawYVals);
        const pad = Math.max(isPct ? 1.5 : 10, (hi - lo) * 0.14);
        yTicks = niceTicks(isPct ? lo - pad : Math.max(0, lo - pad), hi + pad, 6);
        yMin = yTicks[0];
        yMax = yTicks[yTicks.length - 1];
        yToPx = val => margin.top + (1 - (val - yMin) / Math.max(1e-9, yMax - yMin)) * plotH;
      }

      const xToPx = ms => margin.left + ((ms - minX) / Math.max(1, maxX - minX)) * plotW;

      const minDayMs = Math.min(...allPts.map(a => a.pt.dayMs));
      const maxDayMs = Math.max(...allPts.map(a => a.pt.dayMs));
      const totalDaySpan = Math.round((maxDayMs - minDayMs) / 86400000);
      const spanDays = (maxX - minX) / 86400000;
      const maxTicks = Math.min(8, Math.max(3, Math.floor(plotW / 105)));
      const xTicks = [];
      if (singleDay) {
        const centerMs = minDayMs;
        xTicks.push(centerMs - 86400000, centerMs, centerMs + 86400000);
      } else if (totalDaySpan + 1 <= maxTicks) {
        for (let d = 0; d <= totalDaySpan; d++) {
          xTicks.push(minDayMs + d * 86400000);
        }
      } else {
        const dayStep = Math.max(1, Math.ceil(totalDaySpan / (maxTicks - 1)));
        for (let d = 0; d <= totalDaySpan; d += dayStep) {
          xTicks.push(minDayMs + d * 86400000);
        }
        if (xTicks[xTicks.length - 1] < maxDayMs && (maxDayMs - xTicks[xTicks.length - 1]) >= dayStep * 0.45 * 86400000) {
          xTicks.push(maxDayMs);
        }
      }

      const NS = "http://www.w3.org/2000/svg";
      const svg = document.createElementNS(NS, "svg");
      svg.setAttribute("class", "price-svg");
      svg.setAttribute("viewBox", `0 0 ${width} ${height}`);
      svg.setAttribute("width", width);
      svg.setAttribute("height", height);

      function addEl(tag, attrs, parent = svg, text = null) {
        const el = document.createElementNS(NS, tag);
        for (const [k, v] of Object.entries(attrs)) el.setAttribute(k, String(v));
        if (text !== null) el.textContent = text;
        parent.appendChild(el);
        return el;
      }

      // Horizontal grid + Y ticks
      const gridG = addEl("g", {});
      for (const tick of yTicks) {
        const y = yToPx(tick);
        if (y < margin.top - 2 || y > margin.top + plotH + 2) continue;
        addEl("line", {
          x1: margin.left, y1: y, x2: margin.left + plotW, y2: y,
          stroke: "var(--grid)", "stroke-width": 1,
        }, gridG);
        const isIntTick = Math.abs(tick - Math.round(tick)) < 1e-6;
        const label = isPct
          ? (tick > 0 ? `+${tick.toFixed(isIntTick ? 0 : 1)}%` : `${tick.toFixed(isIntTick ? 0 : 1)}%`)
          : "$" + tick.toLocaleString("en-US", {
              minimumFractionDigits: isIntTick ? 0 : 2,
              maximumFractionDigits: isIntTick ? 0 : 2,
            });
        addEl("text", {
          x: margin.left - 10, y: y + 4, "text-anchor": "end",
          fill: "var(--muted)", "font-size": 11.5,
        }, gridG, label);
      }

      // Vertical grid + X ticks
      for (const tx of xTicks) {
        const x = xToPx(tx);
        addEl("line", {
          x1: x, y1: margin.top, x2: x, y2: margin.top + plotH,
          stroke: "var(--grid)", "stroke-width": 1, "stroke-dasharray": "3 3",
        }, gridG);
        addEl("text", {
          x, y: margin.top + plotH + 20, "text-anchor": "middle",
          fill: "var(--muted)", "font-size": 11.5,
        }, gridG, fmtAxisDate(tx, spanDays));
      }

      // Baseline 0% in % Change mode
      if (isPct && 0 >= yMin && 0 <= yMax) {
        const y0 = yToPx(0);
        addEl("line", {
          x1: margin.left, y1: y0, x2: margin.left + plotW, y2: y0,
          stroke: "var(--muted)", "stroke-width": 1.3, "stroke-dasharray": "5 4",
        });
      }

      // $450 SSD DEAL target reference line
      if (showDealTarget && META.dealPriceSsd >= yMin * 0.95 && META.dealPriceSsd <= yMax * 1.05) {
        const yd = yToPx(META.dealPriceSsd);
        addEl("line", {
          x1: margin.left, y1: yd, x2: margin.left + plotW, y2: yd,
          stroke: "var(--warn)", "stroke-width": 1.5, "stroke-dasharray": "6 4",
        });
        addEl("text", {
          x: margin.left + 8, y: yd - 6,
          fill: "var(--warn)", "font-size": 11, "font-weight": 700,
        }, svg, `DEAL target ≤ ${fmtMoney(META.dealPriceSsd)} (4TB TLC SSD)`);
      }

      // Axes frame
      addEl("line", {
        x1: margin.left, y1: margin.top, x2: margin.left, y2: margin.top + plotH,
        stroke: "var(--border)", "stroke-width": 1.2,
      });
      addEl("line", {
        x1: margin.left, y1: margin.top + plotH, x2: margin.left + plotW, y2: margin.top + plotH,
        stroke: "var(--border)", "stroke-width": 1.2,
      });

      // Series lines & moving average
      const labelNodes = [];
      const renderedPts = [];

      plotted.forEach((group, gIdx) => {
        const s = group.series;
        const pts = group.pts;
        const isUsed = s.condition !== "new";
        const isSelected = state.selectedPoint && state.selectedPoint.seriesId === s.id;

        if (pts.length >= 2) {
          const pathD = pts.map((p, i) => `${i === 0 ? "M" : "L"}${xToPx(p.xMs).toFixed(1)},${yToPx(p.yVal).toFixed(1)}`).join(" ");
          addEl("path", {
            d: pathD,
            fill: "none",
            stroke: s.color,
            "stroke-width": isSelected ? 3.2 : 2.3,
            "stroke-linecap": "round",
            "stroke-linejoin": "round",
            ...(isUsed ? { "stroke-dasharray": "6 4" } : {}),
          });
        }

        if (state.showMa && pts.length >= 3) {
          const maPts = movingAveragePoints(pts, 7);
          const maD = maPts.map((p, i) => `${i === 0 ? "M" : "L"}${xToPx(p.xMs).toFixed(1)},${yToPx(p.yVal).toFixed(1)}`).join(" ");
          addEl("path", {
            d: maD,
            fill: "none",
            stroke: s.color,
            "stroke-width": 1.4,
            "stroke-dasharray": "2 3",
            opacity: 0.65,
          });
        }

        // Points
        pts.forEach((p, idx) => {
          const jitter = singleDay && plotted.length > 1
            ? (gIdx - (plotted.length - 1) / 2) * 8
            : 0;
          const cx = xToPx(p.xMs) + jitter;
          const cy = yToPx(p.yVal);
          const isDeal = p.deals && p.deals.length > 0;
          const isPtSelected = isSelected && state.selectedPoint.date === p.activeDate &&
            state.selectedPoint.sameDayIndex === p.sameDayIndex;

          if (isDeal) {
            addEl("circle", {
              cx, cy, r: 9, fill: "none", stroke: "var(--warn)", "stroke-width": 2, opacity: 0.85,
            });
          }

          let marker;
          if (isUsed) {
            marker = addEl("rect", {
              x: cx - 4.5, y: cy - 4.5, width: 9, height: 9, rx: 1.5,
              transform: `rotate(45 ${cx} ${cy})`,
              fill: "var(--surface)", stroke: s.color, "stroke-width": 2.2,
            });
          } else {
            marker = addEl("circle", {
              cx, cy, r: isPtSelected ? 6.5 : (pts.length === 1 ? 6 : 4.3),
              fill: s.color, stroke: "var(--surface)", "stroke-width": 1.8,
            });
          }
          marker.style.cursor = "pointer";

          renderedPts.push({ cx, cy, series: s, pt: p, marker });

          if (state.showLabels && (idx === pts.length - 1 || singleDay)) {
            const valLabel = isPct ? fmtSignedPct(p.yVal) : fmtMoney(p.price);
            // "MacBook Pro 16 M5 Max 128GB": the memory level at the end must stay visible.
            const name = s.item.replace(/^MacBook (?=Pro|Air)/, "");
            const nameShort = name.length > 22 ? name.slice(0, 20) + "…" : name;
            labelNodes.push({
              x: cx,
              y: cy,
              labelY: cy,
              color: s.color,
              text: `${nameShort} · ${valLabel}${isDeal ? " 🔥" : ""}`,
            });
          }
        });
      });

      if (state.showLabels && labelNodes.length) {
        layoutPointLabels(labelNodes, margin.top, margin.top + plotH);
        const labelG = addEl("g", {});
        for (const node of labelNodes) {
          const placeRight = node.x < margin.left + plotW * 0.58;
          const lx = placeRight ? node.x + 12 : node.x - 12;
          if (Math.abs(node.labelY - node.y) > 4 || singleDay) {
            addEl("line", {
              x1: node.x, y1: node.y, x2: placeRight ? lx - 3 : lx + 3, y2: node.labelY - 3,
              stroke: node.color, "stroke-width": 1, opacity: 0.55,
            }, labelG);
          }
          addEl("text", {
            x: lx, y: node.labelY,
            "text-anchor": placeRight ? "start" : "end",
            fill: "var(--text)", "font-size": 11.5, "font-weight": 600,
          }, labelG, node.text);
        }
      }

      // Hover crosshair & overlay
      const crosshair = addEl("line", {
        x1: 0, y1: margin.top, x2: 0, y2: margin.top + plotH,
        stroke: "var(--muted)", "stroke-width": 1, "stroke-dasharray": "4 3",
        visibility: "hidden",
      });
      const focusRing = addEl("circle", {
        cx: 0, cy: 0, r: 8, fill: "none", stroke: "var(--text)", "stroke-width": 1.8,
        visibility: "hidden",
      });

      const overlay = addEl("rect", {
        x: margin.left, y: margin.top, width: plotW, height: plotH,
        fill: "transparent", style: "cursor:crosshair;",
      });

      function findNearest(evt) {
        const rect = svg.getBoundingClientRect();
        const mx = (evt.clientX - rect.left) * (width / rect.width);
        const my = (evt.clientY - rect.top) * (height / rect.height);
        let best = null;
        let bestDist = Infinity;
        for (const rp of renderedPts) {
          const dist = Math.hypot(rp.cx - mx, rp.cy - my);
          if (dist < bestDist) {
            bestDist = dist;
            best = rp;
          }
        }
        return bestDist <= 42 ? best : null;
      }

      overlay.addEventListener("mousemove", evt => {
        const hit = findNearest(evt);
        if (!hit) {
          crosshair.setAttribute("visibility", "hidden");
          focusRing.setAttribute("visibility", "hidden");
          hideTooltip();
          return;
        }
        crosshair.setAttribute("x1", hit.cx);
        crosshair.setAttribute("x2", hit.cx);
        crosshair.setAttribute("visibility", "visible");
        focusRing.setAttribute("cx", hit.cx);
        focusRing.setAttribute("cy", hit.cy);
        focusRing.setAttribute("visibility", "visible");
        showTooltip(evt, hit);
      });

      overlay.addEventListener("mouseleave", () => {
        crosshair.setAttribute("visibility", "hidden");
        focusRing.setAttribute("visibility", "hidden");
        hideTooltip();
      });

      overlay.addEventListener("click", evt => {
        const hit = findNearest(evt);
        if (!hit) return;
        state.selectedPoint = {
          seriesId: hit.series.id,
          date: hit.pt.activeDate,
          sameDayIndex: hit.pt.sameDayIndex,
        };
        updateInspector(hit.series, hit.pt);
        drawSvg();
      });

      svgWrap.innerHTML = "";
      svgWrap.appendChild(svg);
    }

    drawSvg();
    if (window.ResizeObserver) {
      const ro = new ResizeObserver(() => drawSvg());
      ro.observe(svgWrap);
      card._ro = ro;
    }
  }

  function renderTables(filtered) {
    const tbody = document.getElementById("seriesTableBody");
    const rowsData = filtered.map(s => {
      const pts = s.viewPoints;
      const last = pts[pts.length - 1];
      const prices = pts.map(p => p.price);
      return {
        series: s,
        category: s.categoryLabel,
        item: s.item,
        spec: s.spec,
        store: s.store,
        condition: s.condition,
        latest: last.price,
        changePrev: last.viewChangePrev,
        pctPrev: last.viewPctPrev,
        pctFirst: last.viewPctFirst,
        changeFirst: last.viewChangeFirst,
        min: Math.min(...prices),
        max: Math.max(...prices),
        count: pts.length,
        latestDate: last.activeDate,
        url: last.url,
        deals: last.deals,
      };
    });

    rowsData.sort((a, b) => {
      const av = a[state.sortKey];
      const bv = b[state.sortKey];
      let cmp = 0;
      if (av == null && bv == null) cmp = 0;
      else if (av == null) cmp = 1;
      else if (bv == null) cmp = -1;
      else if (typeof av === "number" && typeof bv === "number") cmp = av - bv;
      else cmp = String(av).localeCompare(String(bv));
      return state.sortAsc ? cmp : -cmp;
    });

    document.getElementById("tableCount").textContent = `${rowsData.length} series`;

    tbody.innerHTML = rowsData.map(r => {
      const prevPill = r.changePrev == null
        ? `<span class="pill pill-neutral">first</span>`
        : `<span class="pill ${r.changePrev < 0 ? "pill-good" : r.changePrev > 0 ? "pill-bad" : "pill-neutral"}">${escapeHtml(fmtSignedMoney(r.changePrev))} (${escapeHtml(fmtSignedPct(r.pctPrev))})</span>`;
      const firstPill = r.count < 2
        ? `<span class="pill pill-neutral">—</span>`
        : `<span class="pill ${r.changeFirst < 0 ? "pill-good" : r.changeFirst > 0 ? "pill-bad" : "pill-neutral"}">${escapeHtml(fmtSignedMoney(r.changeFirst))} (${escapeHtml(fmtSignedPct(r.pctFirst))})</span>`;
      const dealTag = r.deals.length ? ` <span class="pill pill-deal" title="${escapeHtml(r.deals.join(", "))}">🔥 DEAL</span>` : "";
      const href = safeUrl(r.url);
      const link = href ? `<a class="ext-link" href="${escapeHtml(href)}" target="_blank" rel="noopener noreferrer" onclick="event.stopPropagation()">link ↗</a>` : "—";
      const selected = state.focusedId === r.series.id ? "selected-row" : "";
      return `
        <tr class="${selected}" data-sid="${escapeHtml(r.series.id)}">
          <td>${escapeHtml(r.category)}</td>
          <td><strong>${escapeHtml(r.item)}</strong>${dealTag}</td>
          <td>${escapeHtml(r.spec)}</td>
          <td>${escapeHtml(r.store)}</td>
          <td>${escapeHtml(r.condition)}</td>
          <td class="num"><strong>${fmtMoney(r.latest)}</strong></td>
          <td class="num">${prevPill}</td>
          <td class="num">${firstPill}</td>
          <td class="num">${fmtMoney(r.min)}</td>
          <td class="num">${fmtMoney(r.max)}</td>
          <td class="num">${r.count}</td>
          <td>${escapeHtml(r.latestDate)}</td>
          <td>${link}</td>
        </tr>
      `;
    }).join("");

    tbody.querySelectorAll("tr").forEach(tr => {
      tr.addEventListener("click", () => {
        const sid = tr.dataset.sid;
        state.focusedId = state.focusedId === sid ? null : sid;
        state.hiddenIds.delete(sid);
        if (!state.focusedId) {
          state.selectedPoint = null;
          updateInspector(null, null);
        } else {
          const s = filtered.find(x => x.id === sid);
          if (s) {
            const last = s.viewPoints[s.viewPoints.length - 1];
            state.selectedPoint = { seriesId: sid, date: last.activeDate, sameDayIndex: last.sameDayIndex };
            updateInspector(s, last);
          }
        }
        render();
      });
    });

    // Observations log
    const allObs = [];
    for (const s of filtered) {
      for (const p of s.viewPoints) {
        allObs.push({ s, p });
      }
    }
    allObs.sort((a, b) => b.p.activeDate.localeCompare(a.p.activeDate) || a.s.category.localeCompare(b.s.category) || a.p.price - b.p.price);
    document.getElementById("logCount").textContent = `${allObs.length} observations`;

    document.getElementById("obsTableBody").innerHTML = allObs.slice(0, 250).map(({ s, p }) => {
      const chg = p.viewChangePrev == null
        ? `<span class="pill pill-neutral">first</span>`
        : `<span class="pill ${p.viewChangePrev < 0 ? "pill-good" : p.viewChangePrev > 0 ? "pill-bad" : "pill-neutral"}">${escapeHtml(fmtSignedMoney(p.viewChangePrev))} (${escapeHtml(fmtSignedPct(p.viewPctPrev))})</span>`;
      const href = safeUrl(p.url);
      const link = href ? `<a class="ext-link" href="${escapeHtml(href)}" target="_blank" rel="noopener noreferrer">source ↗</a>` : "—";
      const dealTag = p.deals.length ? ` 🔥` : "";
      return `
        <tr>
          <td>${escapeHtml(p.activeDate)}</td>
          <td>${escapeHtml(s.categoryLabel)}</td>
          <td><strong>${escapeHtml(s.item)}</strong>${dealTag}</td>
          <td>${escapeHtml(s.store)}</td>
          <td>${escapeHtml(s.condition)}</td>
          <td class="num"><strong>${fmtMoney(p.price)}</strong></td>
          <td class="num">${chg}</td>
          <td>${escapeHtml(p.basis || "—")}</td>
          <td>${escapeHtml(p.sourceDate || "—")}</td>
          <td>${link}</td>
        </tr>
      `;
    }).join("");
  }

  function render() {
    // Cleanup prior ResizeObservers
    document.querySelectorAll(".chart-card").forEach(c => { if (c._ro) c._ro.disconnect(); });

    const filtered = getFilteredSeries();
    renderTabs(filtered);
    updateControlVisibility(filtered);
    renderKpis(filtered);

    const grid = document.getElementById("chartsGrid");
    const banner = document.getElementById("bannerSlot");
    grid.innerHTML = "";
    banner.innerHTML = "";

    const activeSeries = state.metric === "envelope" ? buildEnvelopeSeries(filtered) : filtered;
    if (state.focusedId && !activeSeries.some(s => s.id === state.focusedId)) {
      state.focusedId = null;
    }
    const uniqueDates = Array.from(new Set(activeSeries.flatMap(s => s.viewPoints.map(p => p.activeDate)))).sort();

    if (uniqueDates.length === 1) {
      banner.innerHTML = `<div class="banner">
        <span>Only <strong>1 date (${escapeHtml(uniqueDates[0])})</strong> is currently logged in the filtered view. Points are plotted at today's baseline and will automatically connect into multi-day trend lines as daily updates accumulate in <code>prices.csv</code>.</span>
      </div>`;
    }

    if (!activeSeries.length) {
      grid.className = "charts-grid";
      grid.innerHTML = `<div class="empty-state">No price observations match your current filters.</div>`;
      renderTables([]);
      return;
    }

    const subtitleEl = document.getElementById("subtitle");
    subtitleEl.textContent = `${META.csvName} · ${ALL_SERIES.length} tracked series · Generated ${META.generatedAt}`;

    if (state.category === "all" && state.metric !== "pct") {
      // Per-category small multiples so SSDs ($475) and RTX 5090 ($7,450) each keep a readable Y-axis.
      const byCat = new Map();
      for (const s of activeSeries) {
        if (!byCat.has(s.category)) byCat.set(s.category, []);
        byCat.get(s.category).push(s);
      }
      grid.className = byCat.size > 1 ? "charts-grid multi" : "charts-grid";
      for (const cat of META.categoryOrder) {
        const list = byCat.get(cat);
        if (!list || !list.length) continue;
        const catTitle = (META.categories[cat] && META.categories[cat][0]) || cat;
        const modeTitle = state.metric === "envelope" ? "Daily Cheapest Price" : "Price Over Time (USD)";
        renderChartCard(grid, `${catTitle} — ${modeTitle}`, `${list.length} series`, list, { compact: byCat.size > 1 });
      }
    } else {
      grid.className = "charts-grid";
      const catTitle = state.category === "all"
        ? "All Categories"
        : ((META.categories[state.category] && META.categories[state.category][0]) || state.category);
      const modeTitle = state.metric === "pct"
        ? "% Price Change Since First Logged Date"
        : (state.metric === "envelope" ? "Daily Cheapest Qualifying Price (USD)" : "Price Over Time (USD)");
      renderChartCard(grid, `${catTitle} — ${modeTitle}`, `${activeSeries.length} series`, activeSeries, { compact: false });
    }

    renderTables(filtered);
  }

  // Event bindings
  populateDropdowns();

  document.getElementById("themeBtn").addEventListener("click", () => {
    const cur = document.documentElement.getAttribute("data-theme") || "light";
    applyTheme(cur === "dark" ? "light" : "dark");
    render();
  });

  document.getElementById("resetFocusBtn").addEventListener("click", () => {
    state.focusedId = null;
    state.hiddenIds.clear();
    render();
  });

  document.getElementById("exportSvgBtn").addEventListener("click", () => {
    const svg = document.querySelector("svg.price-svg");
    if (!svg) return;
    const clone = svg.cloneNode(true);
    const bg = getComputedStyle(document.documentElement).getPropertyValue("--surface").trim() || "#ffffff";
    const rect = document.createElementNS("http://www.w3.org/2000/svg", "rect");
    rect.setAttribute("width", "100%");
    rect.setAttribute("height", "100%");
    rect.setAttribute("fill", bg);
    clone.insertBefore(rect, clone.firstChild);
    // Resolve CSS variables on clone elements so exported SVG stands alone.
    const styles = getComputedStyle(document.documentElement);
    const varMap = {};
    ["--text", "--muted", "--grid", "--border", "--surface", "--warn", "--accent"].forEach(v => {
      varMap[`var(${v})`] = styles.getPropertyValue(v).trim();
    });
    clone.querySelectorAll("*").forEach(node => {
      for (const attr of ["stroke", "fill"]) {
        const val = node.getAttribute(attr);
        if (val && varMap[val]) node.setAttribute(attr, varMap[val]);
      }
    });
    const blob = new Blob([new XMLSerializer().serializeToString(clone)], { type: "image/svg+xml;charset=utf-8" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = `price-watch-${state.category}-${state.metric}.svg`;
    a.click();
    setTimeout(() => URL.revokeObjectURL(a.href), 1000);
  });

  document.querySelectorAll("#metricGroup button").forEach(b => {
    b.addEventListener("click", () => {
      state.metric = b.dataset.metric;
      state.focusedId = null;
      state.selectedPoint = null;
      updateInspector(null, null);
      render();
    });
  });
  document.querySelectorAll("#scaleGroup button").forEach(b => {
    b.addEventListener("click", () => { state.scale = b.dataset.scale; render(); });
  });
  document.querySelectorAll("#dateFieldGroup button").forEach(b => {
    b.addEventListener("click", () => { state.dateField = b.dataset.datefield; render(); });
  });
  document.querySelectorAll("#rangeGroup button").forEach(b => {
    b.addEventListener("click", () => { state.rangeDays = b.dataset.range; render(); });
  });

  document.getElementById("condSelect").addEventListener("change", e => { state.condition = e.target.value; render(); });
  document.getElementById("storeSelect").addEventListener("change", e => { state.store = e.target.value; render(); });
  document.getElementById("gpuModelSelect").addEventListener("change", e => { state.gpuModel = e.target.value; render(); });
  document.getElementById("ssdFilterSelect").addEventListener("change", e => { state.ssdFilter = e.target.value; render(); });
  document.getElementById("searchInput").addEventListener("input", e => { state.search = e.target.value; render(); });
  document.getElementById("dealLineCheck").addEventListener("change", e => { state.showDealLine = e.target.checked; render(); });
  document.getElementById("maCheck").addEventListener("change", e => { state.showMa = e.target.checked; render(); });
  document.getElementById("labelsCheck").addEventListener("change", e => { state.showLabels = e.target.checked; render(); });

  document.querySelectorAll("#seriesTable thead th[data-sort]").forEach(th => {
    th.addEventListener("click", () => {
      const k = th.dataset.sort;
      if (state.sortKey === k) state.sortAsc = !state.sortAsc;
      else { state.sortKey = k; state.sortAsc = true; }
      render();
    });
  });

  render();
})();
</script>
</body>
</html>
"""


def render_html(csv_path, cats, series_list, initial_metric="price"):
    """Build the self-contained interactive HTML visualization string."""
    payload = {
        "meta": {
            "csvName": csv_path.name,
            "generatedAt": dt.datetime.now().strftime("%Y-%m-%d %H:%M"),
            "dealPriceSsd": build_readme.DEAL_PRICE,
            "dealDropPct": build_readme.DEAL_DROP * 100,
            "atlMinDays": build_readme.ATL_MIN_DAYS,
            "categories": build_readme.CATEGORIES,
            "categoryOrder": cats,
            "gpuModels": build_readme.GPU_MODELS,
            "initial": {
                "category": "all",
                "metric": initial_metric,
            },
        },
        "series": series_list,
    }
    safe_json = json.dumps(payload, ensure_ascii=False).replace("</", "<\\/")
    page_title = html.escape(f"Price Watch — {csv_path.name}")
    return (
        HTML_TEMPLATE
        .replace("__PAGE_TITLE__", page_title)
        .replace("__PAYLOAD_JSON__", safe_json)
    )


def build_arg_parser():
    parser = argparse.ArgumentParser(
        description="Visualize price changes over time from prices.csv."
    )
    parser.add_argument(
        "--csv",
        type=Path,
        default=DEFAULT_CSV,
        help=f"Path to prices CSV (default: {DEFAULT_CSV})",
    )
    parser.add_argument(
        "-o", "--out",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=f"Output HTML file path (default: {DEFAULT_OUTPUT})",
    )
    parser.add_argument(
        "--no-open",
        action="store_true",
        help="Generate the HTML chart without opening a web browser.",
    )
    parser.add_argument(
        "--terminal",
        action="store_true",
        help="Print terminal summary and ASCII price-vs-time charts only (no HTML/browser).",
    )
    parser.add_argument(
        "--category",
        default="all",
        help="Filter to a category (ssd, ram, nvidia_gpu, amd_gpu, egpu, macbook, or all).",
    )
    parser.add_argument(
        "--item",
        default="",
        help="Filter to items/specs containing this text (case-insensitive).",
    )
    parser.add_argument(
        "--store",
        default="",
        help="Filter to stores containing this text (case-insensitive).",
    )
    parser.add_argument(
        "--condition",
        choices=("all", "new", "used"),
        default="all",
        help="Filter by condition (default: all).",
    )
    parser.add_argument(
        "--since",
        default="",
        help="Include rows on or after YYYY-MM-DD.",
    )
    parser.add_argument(
        "--until",
        default="",
        help="Include rows on or before YYYY-MM-DD.",
    )
    parser.add_argument(
        "--metric",
        choices=("price", "pct", "envelope"),
        default="price",
        help="Initial chart metric: price ($), pct (%% change), or envelope (daily cheapest).",
    )
    return parser


def main(argv=None):
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    try:
        raw_rows, skipped = load_rows(args.csv)
    except FileNotFoundError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    if skipped:
        print(f"Warning: skipped {skipped} malformed row(s) in {args.csv}.", file=sys.stderr)

    enriched = enrich_rows(raw_rows)
    try:
        filtered = filter_rows(enriched, args)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2

    cats, series_list = build_series_payload(filtered)
    print_terminal_summary(filtered, series_list, cats, args.csv, show_charts=args.terminal)

    if args.terminal:
        return 0

    out_path = args.out.expanduser().resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    html_text = render_html(args.csv, cats, series_list, initial_metric=args.metric)
    out_path.write_text(html_text, encoding="utf-8")
    print(f"\nDashboard written to: {out_path}")

    if not args.no_open:
        opened = webbrowser.open(out_path.as_uri())
        if opened:
            print("Opened visualization in your default browser.")
        else:
            print("Could not launch browser automatically; open the file path above manually.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
