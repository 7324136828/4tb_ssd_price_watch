#!/usr/bin/env python3
"""Regenerate the price dashboard section of README.md from prices.csv.

Everything between the PRICES:START and PRICES:END markers is replaced.
Text outside the markers is left alone. Uses only the standard library.

prices.csv columns:
    date,category,item,spec,store,condition,price_usd,basis,source_date,url
category is one of ssd, ram, nvidia_gpu, amd_gpu, egpu.
"""
import csv
import math
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CSV_PATH = ROOT / "prices.csv"
README_PATH = ROOT / "README.md"
START = "<!-- PRICES:START -->"
END = "<!-- PRICES:END -->"

DEAL_PRICE = 450.0      # ssd only: new 4TB TLC at or below this price
DEAL_DROP = 0.10        # any category: at least 10% below the previous price
ATL_MIN_DAYS = 7        # any category: all-time-low rule needs this many days of history

# category -> (section heading, singular noun used in sentences)
CATEGORIES = {
    "ssd": ("SSDs", "SSD"),
    "ram": ("RAM", "64GB DDR5 SO-DIMM"),
    "nvidia_gpu": ("NVIDIA GPUs", "NVIDIA GPU"),
    "amd_gpu": ("AMD GPUs", "AMD GPU"),
    "egpu": ("eGPUs", "eGPU"),
}


def cat_names(cat):
    return CATEGORIES.get(cat, (cat, cat))


# Tracked GPU models per category, in display order. Every model gets a row in
# the model summary, even before a price has been logged for it.
GPU_MODELS = {
    "nvidia_gpu": ["RTX 5090", "RTX 4090", "RTX 3090 Ti", "RTX 3090"],
    "amd_gpu": ["RX 9070 XT", "RX 9070", "RX 7900 XTX", "RX 7900 XT"],
}
GPU_MODEL_RE = re.compile(
    r"\b(RTX|RX)\s*-?\s*(\d{4})(?:\s*-?\s*(Ti\s*Super|Ti|Super|XTX|XT|GRE|D))?\b",
    re.IGNORECASE)
SUFFIX_CASE = {"ti super": "Ti Super", "ti": "Ti", "super": "Super", "xtx": "XTX",
               "xt": "XT", "gre": "GRE", "d": "D"}


def gpu_model(r):
    """Normalised GPU model from item (then spec), e.g. 'RTX 3090 Ti', 'RX 9070 XT'."""
    for text in (r.get("item"), r.get("spec")):
        m = GPU_MODEL_RE.search(text or "")
        if m:
            suffix = re.sub(r"\s+", " ", (m.group(3) or "")).lower()
            model = f"{m.group(1).upper()} {m.group(2)}"
            return f"{model} {SUFFIX_CASE[suffix]}" if suffix else model
    return "Other"


def model_order(cat, models):
    tracked = GPU_MODELS.get(cat, [])
    return tracked + sorted(m for m in set(models) if m not in tracked)


def load_rows():
    if not CSV_PATH.exists():
        return []
    with CSV_PATH.open(newline="", encoding="utf-8") as f:
        rows = []
        for r in csv.DictReader(f):
            try:
                r["price"] = float(r["price_usd"])
            except (KeyError, TypeError, ValueError):
                continue
            for k in ("date", "category", "item", "spec", "store", "condition", "basis", "url"):
                r[k] = (r.get(k) or "").strip()
            r["category"] = r["category"].lower()
            rows.append(r)
    return rows


def money(x):
    return f"${x:,.2f}"


def esc(s):
    return (s or "").replace("|", "\\|")


def is_tlc(spec):
    return re.search(r"\bTLC\b", spec or "", re.IGNORECASE) is not None


def capacity_tb(spec):
    """Capacity in TB parsed from the spec text (e.g. '4TB TLC', '2 TB'), or 0."""
    m = re.search(r"(\d+(?:\.\d+)?)\s*TB\b", spec or "", re.IGNORECASE)
    if m:
        return float(m.group(1))
    m = re.search(r"(\d+(?:\.\d+)?)\s*GB\b", spec or "", re.IGNORECASE)
    return float(m.group(1)) / 1000 if m else 0.0


def is_4tb_ssd(r):
    return r["category"] == "ssd" and capacity_tb(r["spec"]) >= 4


def series_key(r):
    return (r["category"], r["item"], r["store"], r["condition"])


def mermaid_label(s):
    return '"' + s.replace('"', "'") + '"'


def axis_range(values):
    lo, hi = min(values), max(values)
    pad = max(10.0, (hi - lo) * 0.15)
    lo = max(0, math.floor((lo - pad) / 10) * 10)
    hi = math.ceil((hi + pad) / 10) * 10
    return lo, hi


def category_order(rows):
    seen = {r["category"] for r in rows}
    known = [c for c in CATEGORIES if c in seen]
    return known + sorted(seen - set(CATEGORIES))


def deal_reasons(cur, prev, earlier_item_prices, history_days):
    """Why the latest row of a series is a DEAL (empty list = not a deal)."""
    reasons = []
    if (cur["category"] == "ssd" and cur["condition"] == "new" and is_tlc(cur["spec"])
            and capacity_tb(cur["spec"]) >= 4 and cur["price"] <= DEAL_PRICE):
        reasons.append(f"4TB TLC ≤ {money(DEAL_PRICE)}")
    if prev is not None and cur["price"] <= prev["price"] * (1 - DEAL_DROP):
        reasons.append(f"≥{DEAL_DROP:.0%} drop")
    if (history_days >= ATL_MIN_DAYS and earlier_item_prices
            and cur["price"] < min(earlier_item_prices)):
        reasons.append("all-time low")
    return reasons


def analyse(rows):
    """Latest row per series with its previous row, change and DEAL reasons."""
    all_days = sorted({r["date"] for r in rows})

    history = defaultdict(list)
    for r in rows:
        history[series_key(r)].append(r)
    for hist in history.values():
        hist.sort(key=lambda r: r["date"])  # stable: keeps file order within a day

    latest = []
    for key, hist in history.items():
        cur = hist[-1]
        prev = hist[-2] if len(hist) > 1 else None
        change = None if prev is None else cur["price"] - prev["price"]
        # Earlier prices for the same item and condition, at any store.
        earlier = [r["price"] for r in rows
                   if r is not cur and r["category"] == cur["category"]
                   and r["item"] == cur["item"] and r["condition"] == cur["condition"]
                   and r["date"] < cur["date"]]
        # Days of history in prices.csv as of this row's date.
        history_days = sum(1 for d in all_days if d <= cur["date"])
        reasons = deal_reasons(cur, prev, earlier, history_days)
        latest.append({"row": cur, "prev": prev, "change": change, "deal": reasons})
    latest.sort(key=lambda t: (t["row"]["category"], t["row"]["price"]))
    return history, latest


def chart(out, heading, title, labels, values, kind):
    lo, hi = axis_range(values)
    out.append(f"#### {heading}")
    out.append("")
    out.append("```mermaid")
    out.append("xychart-beta")
    out.append(f"    title {mermaid_label(title)}")
    out.append("    x-axis [" + ", ".join(mermaid_label(l) for l in labels) + "]")
    out.append(f'    y-axis "USD" {lo} --> {hi}')
    data = ", ".join(f"{v:.2f}" for v in values)
    if kind == "line":
        out.append(f"    line [{data}]")
        if len(values) == 1:
            out.append(f"    bar [{data}]")
    else:
        out.append(f"    bar [{data}]")
    out.append("```")
    out.append("")


def build_gpu_models(out, cat, cat_rows, cat_latest):
    """Per-model summary for a GPU category: cheapest new and used, plus charts."""
    by_model = defaultdict(list)
    for t in cat_latest:
        by_model[gpu_model(t["row"])].append(t)
    models = model_order(cat, by_model)

    def cell(ts):
        if not ts:
            return "—"
        t = min(ts, key=lambda t: t["row"]["price"])
        r = t["row"]
        return (f"[{money(r['price'])}]({r['url']}){' 🔥' if t['deal'] else ''} "
                f"{esc(r['store'])}, {r['date']}")

    out.append("#### Cheapest by model")
    out.append("")
    out.append("| Model | Cheapest new | Cheapest used / refurbished |")
    out.append("|---|---|---|")
    for m in models:
        ts = by_model.get(m, [])
        new = [t for t in ts if t["row"]["condition"] == "new"]
        used = [t for t in ts if t["row"]["condition"] != "new"]
        out.append(f"| {esc(m)} | {cell(new)} | {cell(used)} |")
    out.append("")
    out.append("<sub>Uses the most recent logged price for each item, store and condition.</sub>")
    out.append("")

    # Bar chart: cheapest current new price per model.
    best = []
    for m in models:
        new = [t["row"]["price"] for t in by_model.get(m, []) if t["row"]["condition"] == "new"]
        if new:
            best.append((m, min(new)))
    if best:
        chart(out, "Latest new price by model (cheapest store)",
              "Most recent logged new price (USD)",
              [m for m, _ in best], [p for _, p in best], "bar")

    # Line chart per model: cheapest new price per day.
    trends = []
    for m in models:
        by_day = defaultdict(list)
        for r in cat_rows:
            if r["condition"] == "new" and gpu_model(r) == m:
                by_day[r["date"]].append(r["price"])
        if by_day:
            trends.append((m, by_day))
    if trends:
        out.append("<details>")
        out.append("<summary><b>New price over time, by model</b></summary>")
        out.append("")
        for m, by_day in trends:
            days = sorted(by_day)[-60:]
            chart(out, f"{esc(m)}: cheapest new price over time",
                  f"Lowest new {m} price per day (USD)",
                  [d[5:] for d in days], [min(by_day[d]) for d in days], "line")
        out.append("</details>")
        out.append("")


def build_category(out, cat, rows, history, latest, latest_date):
    name, noun = cat_names(cat)
    cat_rows = [r for r in rows if r["category"] == cat]
    cat_latest = [t for t in latest if t["row"]["category"] == cat]
    ssd = cat == "ssd"
    gpu = cat in GPU_MODELS
    if gpu:  # group the table by model, cheapest first within each model
        order = {m: i for i, m in enumerate(model_order(cat, [gpu_model(t["row"]) for t in cat_latest]))}
        cat_latest = sorted(cat_latest, key=lambda t: (order[gpu_model(t["row"])], t["row"]["price"]))

    out.append(f"### {name}")
    out.append("")

    # Callout: cheapest new price on the latest check (4TB, preferring TLC, for SSDs).
    today_new = [t["row"] for t in cat_latest
                 if t["row"]["date"] == latest_date and t["row"]["condition"] == "new"
                 and (not ssd or is_4tb_ssd(t["row"]))]
    tlc_today = [r for r in today_new if is_tlc(r["spec"])] if ssd else []
    pool = tlc_today or today_new
    what = ("new 4TB " + ("TLC " if tlc_today else "") + "SSD") if ssd else f"new {noun}"
    if pool:
        b = min(pool, key=lambda r: r["price"])
        out.append(f"> **Cheapest {what} on {latest_date}:** {esc(b['item'])} "
                   f"({esc(b['spec'])}) at **{money(b['price'])}** ({esc(b['store'])}) — "
                   f"[source]({b['url']})")
    else:
        out.append(f"> No new {'4TB SSD' if ssd else noun} price was found on {latest_date}.")
    out.append("")

    # Chart: cheapest new price per day.
    by_day = defaultdict(list)
    for r in cat_rows:
        if r["condition"] == "new" and (not ssd or is_4tb_ssd(r)):
            by_day[r["date"]].append(r["price"])
    days = sorted(by_day)[-60:]
    if gpu:
        build_gpu_models(out, cat, cat_rows, cat_latest)
    elif days:
        label = "new 4TB SSD" if ssd else f"new {noun}"
        chart(out, f"Cheapest {label} price over time",
              f"Lowest {label} price per day (USD)",
              [d[5:] for d in days], [min(by_day[d]) for d in days], "line")

    # Chart: latest price per item (new, cheapest store).
    best_per_item = {}
    for t in cat_latest:
        cur = t["row"]
        if cur["condition"] != "new" or (ssd and not is_4tb_ssd(cur)):
            continue
        if cur["item"] not in best_per_item or cur["price"] < best_per_item[cur["item"]]["price"]:
            best_per_item[cur["item"]] = cur
    if best_per_item and not gpu:
        items = sorted(best_per_item.values(), key=lambda r: r["price"])
        chart(out, "Latest price by item (new, cheapest store)",
              "Most recent logged price (USD)",
              [r["item"] for r in items], [r["price"] for r in items], "bar")

    # Table: latest price for every item/store/condition.
    out.append("#### Latest prices")
    out.append("")
    model_col = "| Model " if gpu else ""
    out.append(f"{model_col}| Item | Spec | Store | Condition | Price | Change | As of | Basis | Link |")
    out.append(("|---" if gpu else "") + "|---|---|---|---|--:|--:|---|---|---|")
    for t in cat_latest:
        cur, change = t["row"], t["change"]
        if change is None:
            ch = "new"
        elif abs(change) < 0.005:
            ch = "—"
        else:
            ch = f"{'🔻' if change < 0 else '🔺'} {money(abs(change))}"
        price = money(cur["price"]) + (" 🔥" if t["deal"] else "")
        model_cell = f"| {esc(gpu_model(cur))} " if gpu else ""
        out.append(
            f"{model_cell}| {esc(cur['item'])} | {esc(cur['spec'])} | {esc(cur['store'])} | "
            f"{esc(cur['condition'])} | **{price}** | {ch} | {cur['date']} | "
            f"{esc(cur['basis'])} | [link]({cur['url']}) |"
        )
    out.append("")

    # Collapsible full history per item.
    out.append("<details>")
    out.append(f"<summary><b>{esc(name)}: price history</b></summary>")
    out.append("")
    for key in sorted(k for k in history if k[0] == cat):
        _, item, store, cond = key
        hist = history[key]
        prices = [r["price"] for r in hist]
        out.append(f"##### {esc(item)} — {esc(store)} ({esc(cond)})")
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


def build(rows):
    if not rows:
        return "_No prices logged yet._"

    latest_date = max(r["date"] for r in rows)
    history, latest = analyse(rows)
    cats = category_order(rows)

    out = []
    out.append(f"**Last check:** {latest_date} &nbsp;·&nbsp; "
               f"**Prices logged:** {len(rows)} &nbsp;·&nbsp; "
               f"**Items tracked with prices:** "
               f"{len({(r['category'], r['item']) for r in rows})} "
               f"across {len(cats)} categor{'y' if len(cats) == 1 else 'ies'}")
    out.append("")
    deals = [t for t in latest if t["deal"] and t["row"]["date"] == latest_date]
    out.append("> " + ("🔥 **DEAL:** " + "; ".join(
        f"{esc(t['row']['item'])} {money(t['row']['price'])} at {esc(t['row']['store'])} "
        f"({', '.join(t['deal'])})" for t in deals)
        if deals else "No DEAL flags on the latest check."))
    out.append("")
    out.append("| Category | Latest-check rows | Cheapest new on latest check |")
    out.append("|---|--:|---|")
    for cat in cats:
        todays = [r for r in rows if r["category"] == cat and r["date"] == latest_date]
        new = [r for r in todays if r["condition"] == "new"
               and (cat != "ssd" or is_4tb_ssd(r))]
        cheapest = min(new, key=lambda r: r["price"]) if new else None
        out.append(f"| {esc(cat_names(cat)[0])} | {len(todays)} | "
                   + (f"{esc(cheapest['item'])} — {money(cheapest['price'])} "
                      f"({esc(cheapest['store'])})" if cheapest else "—") + " |")
    out.append("")

    for cat in cats:
        build_category(out, cat, rows, history, latest, latest_date)

    out.append(f"🔥 = DEAL: a new 4TB TLC SSD at {money(DEAL_PRICE)} or less (SSDs only); "
               f"or, in any category, a price at least {DEAL_DROP:.0%} below the previous "
               f"logged price for the same item, store and condition, or strictly below every "
               f"earlier price for that item and condition once prices.csv has at least "
               f"{ATL_MIN_DAYS} days of history. Change is against the previous logged price "
               f"for the same item, store and condition.")
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
