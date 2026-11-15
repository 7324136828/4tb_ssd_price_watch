#!/usr/bin/env python3
"""Regenerate the price dashboard section of README.md from prices.csv.

Everything between the PRICES:START and PRICES:END markers is replaced.
Text outside the markers is left alone. Uses only the standard library.
"""
import csv
import math
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CSV_PATH = ROOT / "prices.csv"
README_PATH = ROOT / "README.md"
START = "<!-- PRICES:START -->"
END = "<!-- PRICES:END -->"

DEAL_PRICE = 450.0
DEAL_DROP = 0.10


def load_rows():
    if not CSV_PATH.exists():
        return []
    with CSV_PATH.open(newline="", encoding="utf-8") as f:
        rows = []
        for r in csv.DictReader(f):
            try:
                r["price"] = float(r["price_usd"])
            except (KeyError, ValueError):
                continue
            rows.append(r)
    return rows


def money(x):
    return f"${x:,.2f}"


def esc(s):
    return (s or "").replace("|", "\\|")


def is_tlc(flash):
    return (flash or "").strip().upper().startswith("TLC")


def series_key(r):
    return (r["drive"], r["store"], r["condition"])


def mermaid_label(s):
    return '"' + s.replace('"', "'") + '"'


def axis_range(values):
    lo, hi = min(values), max(values)
    pad = max(10.0, (hi - lo) * 0.15)
    lo = max(0, math.floor((lo - pad) / 10) * 10)
    hi = math.ceil((hi + pad) / 10) * 10
    return lo, hi


def build(rows):
    if not rows:
        return "_No prices logged yet._"

    latest_date = max(r["date"] for r in rows)

    # Full history per (drive, store, condition), in file order.
    history = defaultdict(list)
    for r in rows:
        history[series_key(r)].append(r)

    # Latest row of each series, with change vs the previous row of that series.
    latest = []
    for key, hist in history.items():
        cur = hist[-1]
        prev = hist[-2] if len(hist) > 1 else None
        change = None if prev is None else cur["price"] - prev["price"]
        deal = (
            cur["condition"] == "new"
            and is_tlc(cur["flash"])
            and float(cur.get("capacity_tb") or 0) >= 4
            and cur["price"] <= DEAL_PRICE
        ) or (prev is not None and cur["price"] <= prev["price"] * (1 - DEAL_DROP))
        latest.append((cur, prev, change, deal))
    latest.sort(key=lambda t: t[0]["price"])

    new_today = [t for t in latest if t[0]["date"] == latest_date and t[0]["condition"] == "new"
                 and float(t[0].get("capacity_tb") or 0) >= 4]
    tlc_today = [t for t in new_today if is_tlc(t[0]["flash"])]
    best = (tlc_today or new_today or [None])[0]

    out = []
    out.append(f"**Last check:** {latest_date} &nbsp;·&nbsp; "
               f"**Prices logged:** {len(rows)} &nbsp;·&nbsp; "
               f"**Drives tracked with prices:** {len({r['drive'] for r in rows})}")
    out.append("")
    if best:
        b = best[0]
        out.append(f"> **Cheapest new 4TB {'TLC ' if tlc_today else ''}drive on {latest_date}:** "
                   f"{esc(b['drive'])} at **{money(b['price'])}** ({esc(b['store'])}) — "
                   f"[source]({b['url']})")
    else:
        out.append(f"> No new 4TB price was found on {latest_date}.")
    deals = [t for t in latest if t[3] and t[0]["date"] == latest_date]
    out.append(">")
    out.append("> " + ("🔥 **DEAL:** " + ", ".join(
        f"{esc(t[0]['drive'])} {money(t[0]['price'])} at {esc(t[0]['store'])}" for t in deals)
        if deals else "No DEAL flags on the latest check."))
    out.append("")

    # Chart: cheapest new 4TB price per day.
    by_day = defaultdict(list)
    for r in rows:
        if r["condition"] == "new" and float(r.get("capacity_tb") or 0) >= 4:
            by_day[r["date"]].append(r["price"])
    days = sorted(by_day)[-60:]
    if days:
        vals = [min(by_day[d]) for d in days]
        lo, hi = axis_range(vals)
        out.append("### Cheapest new 4TB price over time")
        out.append("")
        out.append("```mermaid")
        out.append("xychart-beta")
        out.append('    title "Lowest new 4TB price per day (USD)"')
        out.append("    x-axis [" + ", ".join(mermaid_label(d[5:]) for d in days) + "]")
        out.append(f'    y-axis "USD" {lo} --> {hi}')
        out.append("    line [" + ", ".join(f"{v:.2f}" for v in vals) + "]")
        if len(days) == 1:
            out.append("    bar [" + ", ".join(f"{v:.2f}" for v in vals) + "]")
        out.append("```")
        out.append("")

    # Chart: latest price per drive (new, cheapest store).
    best_per_drive = {}
    for cur, _, _, _ in latest:
        if cur["condition"] != "new" or float(cur.get("capacity_tb") or 0) < 4:
            continue
        d = cur["drive"]
        if d not in best_per_drive or cur["price"] < best_per_drive[d]["price"]:
            best_per_drive[d] = cur
    if best_per_drive:
        items = sorted(best_per_drive.values(), key=lambda r: r["price"])
        lo, hi = axis_range([r["price"] for r in items])
        out.append("### Latest 4TB price by drive (new, cheapest store)")
        out.append("")
        out.append("```mermaid")
        out.append("xychart-beta")
        out.append('    title "Most recent logged price (USD)"')
        out.append("    x-axis [" + ", ".join(mermaid_label(r["drive"]) for r in items) + "]")
        out.append(f'    y-axis "USD" {lo} --> {hi}')
        out.append("    bar [" + ", ".join(f"{r['price']:.2f}" for r in items) + "]")
        out.append("```")
        out.append("")

    # Table: latest price for every drive/store/condition.
    out.append("### Latest prices")
    out.append("")
    out.append("| Drive | Flash | Store | Condition | Price | Change | As of | Basis | Link |")
    out.append("|---|---|---|---|--:|--:|---|---|---|")
    for cur, prev, change, deal in latest:
        if change is None:
            ch = "new"
        elif abs(change) < 0.005:
            ch = "—"
        else:
            arrow = "🔻" if change < 0 else "🔺"
            ch = f"{arrow} {money(abs(change))}"
        price = money(cur["price"]) + (" 🔥" if deal else "")
        out.append(
            f"| {esc(cur['drive'])} | {esc(cur['flash'])} | {esc(cur['store'])} | "
            f"{esc(cur['condition'])} | **{price}** | {ch} | {cur['date']} | "
            f"{esc(cur['basis'])} | [link]({cur['url']}) |"
        )
    out.append("")
    out.append("🔥 = DEAL (new 4TB TLC at $450 or less, or at least 10% below its previous price). "
               "Change is against the previous logged price for the same drive, store and condition.")
    out.append("")

    # Collapsible full history per drive.
    out.append("<details>")
    out.append("<summary><b>Price history by drive</b></summary>")
    out.append("")
    for key in sorted(history, key=lambda k: (k[0], k[1], k[2])):
        drive, store, cond = key
        hist = history[key]
        prices = [r["price"] for r in hist]
        out.append(f"#### {esc(drive)} — {esc(store)} ({esc(cond)})")
        out.append(f"Low {money(min(prices))} · High {money(max(prices))} · {len(hist)} entr"
                   f"{'y' if len(hist) == 1 else 'ies'}")
        out.append("")
        out.append("| Date | Price | Basis |")
        out.append("|---|--:|---|")
        for r in reversed(hist[-30:]):
            out.append(f"| {r['date']} | [{money(r['price'])}]({r['url']}) | {esc(r['basis'])} |")
        out.append("")
    out.append("</details>")
    out.append("")
    out.append(f"<sub>Generated from [`prices.csv`](prices.csv) by "
               f"[`scripts/build_readme.py`](scripts/build_readme.py). "
               f"Daily notes are in [`claude.md`](claude.md).</sub>")
    return "\n".join(out)


def main():
    readme = README_PATH.read_text(encoding="utf-8") if README_PATH.exists() else ""
    section = f"{START}\n{build(load_rows())}\n{END}"
    if START in readme and END in readme:
        head, rest = readme.split(START, 1)
        _, tail = rest.split(END, 1)
        new = head + section + tail
    else:
        new = readme.rstrip("\n") + "\n\n" + section + "\n"
    if new != readme:
        README_PATH.write_text(new, encoding="utf-8")
        print("README.md updated")
    else:
        print("README.md unchanged")
    return 0


if __name__ == "__main__":
    sys.exit(main())
