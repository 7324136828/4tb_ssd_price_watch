# Nitro V 16S Upgrade Price Watch

Daily US prices (USD) for upgrades and GPUs for an Acer Nitro V 16S (ANV16S-71), in five categories:

| Category | What's tracked |
|---|---|
| `ssd` | 4TB M.2 2280 NVMe PCIe 4.0 SSDs without a heatsink (Lexar NM790, TeamGroup MP44 and T-Force G50, WD Black SN7100 and SN850X, WD Blue SN5000, Samsung 990 EVO Plus and 990 Pro, Crucial T500 and P310, Kingston KC3000, Silicon Power UD90 and other reputable brands), plus the Micron 2500 |
| `ram` | Single 64GB DDR5 SO-DIMM modules, non-ECC, 5600 MT/s or faster |
| `nvidia_gpu` | Desktop RTX 5090, 4090, 3090 Ti and 3090, new and used/refurbished |
| `amd_gpu` | Desktop RX 9070 XT, 9070, 7900 XTX and 7900 XT (plus any newer Radeon above the 9070 XT), new and used/refurbished |
| `egpu` | Thunderbolt/USB4 eGPU enclosures and complete external GPUs |

Stores: Amazon, eBay, Newegg, Best Buy, Walmart, B&H Photo and Micro Center.

**DEAL flags (🔥):**
- A new 4TB TLC SSD at $450 or less (SSDs only).
- In any category, a price at least 10% below the previous logged price for the same item, store and condition.
- In any category, a price strictly below every earlier price for that item and condition, once there are at least 7 days of history.

## How it works

- A daily routine adds prices to [`prices.csv`](prices.csv) (`date,category,item,spec,store,condition,price_usd,basis,source_date,url`) and writes notes to [`claude.md`](claude.md).
- [`scripts/build_readme.py`](scripts/build_readme.py) rebuilds the dashboard below. GPUs are grouped by model.
- The [Update README dashboard](.github/workflows/update-readme.yml) Action runs the script whenever `prices.csv` or the script changes on `main`. To run it yourself:

```bash
python3 scripts/build_readme.py
```

Only the text between the `PRICES:START` and `PRICES:END` markers is regenerated. Everything above them can be edited by hand.

### GPU price tracker

[`scripts/track_gpus.py`](scripts/track_gpus.py) checks the RTX 5090, 4090, 3090 Ti and 3090 and the RX 9070 XT, 9070, 7900 XTX and 7900 XT on [videocardprices.com](https://videocardprices.com/). It also picks up any newer Radeon card numbered 9080 or higher. It logs in-stock Amazon and Newegg prices that are dated within 2 days. eBay used listings are only reported, because the script can't check the seller. The [Track GPU prices](.github/workflows/track-gpus.yml) Action runs it every day and rebuilds the dashboard.

```bash
python3 scripts/track_gpus.py            # dry run: show what would be logged
python3 scripts/track_gpus.py --write    # append new rows to prices.csv
```

The source doesn't cover the RTX 4090, 3090 Ti, 3090 or RX 7900 XT, and the tracker lists them as "check by hand". Log those prices, and any eBay listing you have checked, with [`scripts/add_price.py`](scripts/add_price.py). It applies the same rules:

```bash
python3 scripts/add_price.py nvidia_gpu "RTX 4090 (MSI Gaming X Trio)" "24GB GDDR6X" eBay used 1899.00 "https://www.ebay.com/itm/..."
```

Run the tests with `python3 -m unittest discover tests`.

## Dashboard

<!-- PRICES:START -->
**Last check:** 2026-11-15 &nbsp;·&nbsp; **Prices logged:** 26 &nbsp;·&nbsp; **Items tracked with prices:** 13 across 3 categories

> No DEAL flags on the latest check.

| Category | Latest-check rows | Cheapest new on latest check |
|---|--:|---|
| SSDs | 12 | Silicon Power UD90 — $475.00 (Newegg) |
| NVIDIA GPUs | 1 | RTX 5090 (ASUS TUF Gaming OC) — $7,450.00 (Amazon) |
| AMD GPUs | 1 | RX 9070 XT (GIGABYTE Gaming OC) — $1,034.99 (Amazon) |

### SSDs

> **Cheapest new 4TB TLC SSD on 2026-11-15:** Silicon Power UD90 (4TB TLC (some batches reported QLC)) at **$475.00** (Newegg) — [source](https://www.pcgamer.com/black-friday-ssd-deals/)

#### Cheapest new 4TB SSD price over time

```mermaid
xychart-beta
    title "Lowest new 4TB SSD price per day (USD)"
    x-axis ["11-14", "11-15"]
    y-axis "USD" 460 --> 490
    line [474.97, 475.00]
```

#### Latest price by item (new, cheapest store)

```mermaid
xychart-beta
    title "Most recent logged price (USD)"
    x-axis ["Silicon Power UD90", "WD Blue SN5000", "TeamGroup MP44Q", "TeamGroup MP44", "WD Blue SN5100", "WD Black SN7100", "Samsung 990 EVO Plus", "WD Black SN850X", "Samsung 990 Pro", "Crucial T500"]
    y-axis "USD" 410 --> 930
    bar [475.00, 491.00, 499.99, 516.99, 529.99, 629.99, 649.99, 784.99, 799.99, 869.00]
```

#### Latest prices

| Item | Spec | Store | Condition | Price | Change | As of | Basis | Link |
|---|---|---|---|--:|--:|---|---|---|
| Silicon Power UD90 | 4TB TLC (some batches reported QLC) | Newegg | new | **$475.00** | — | 2026-11-15 | reported (PC Gamer) | [link](https://www.pcgamer.com/black-friday-ssd-deals/) |
| WD Blue SN5000 | 4TB QLC | Newegg | new | **$491.00** | — | 2026-11-15 | reported (PC Gamer) | [link](https://www.pcgamer.com/black-friday-ssd-deals/) |
| TeamGroup MP44Q | 4TB QLC | Amazon | new | **$499.99** | — | 2026-11-15 | reported (PC Gamer) | [link](https://www.pcgamer.com/black-friday-ssd-deals/) |
| TeamGroup MP44 | 4TB TLC | Newegg | new | **$516.99** | — | 2026-11-15 | reported (PC Gamer) | [link](https://www.pcgamer.com/black-friday-ssd-deals/) |
| Silicon Power UD90 | 4TB TLC (some batches reported QLC) | Amazon | new | **$529.97** | 🔺 $55.00 | 2026-11-15 | reported (cheapestssd.com) | [link](https://cheapestssd.com/4tb-nvme-ssd/) |
| WD Blue SN5100 | 4TB QLC | Amazon | new | **$529.99** | new | 2026-11-15 | reported (cheapestssd.com) | [link](https://cheapestssd.com/4tb-nvme-ssd/) |
| WD Black SN7100 | 4TB TLC | Amazon | new | **$629.99** | new | 2026-11-15 | reported (cheapestssd.com) | [link](https://cheapestssd.com/4tb-nvme-ssd/) |
| Samsung 990 EVO Plus | 4TB TLC | B&H Photo | new | **$649.99** | — | 2026-11-15 | reported (9to5Toys) | [link](https://9to5toys.com/2026/11/14/this-weeks-pc-deals-and-news/) |
| Samsung 990 EVO Plus | 4TB TLC | Amazon | new | **$679.99** | new | 2026-11-15 | reported (cheapestssd.com) | [link](https://cheapestssd.com/4tb-nvme-ssd/) |
| WD Black SN850X | 4TB TLC | Amazon | new | **$784.99** | new | 2026-11-15 | reported (cheapestssd.com) | [link](https://cheapestssd.com/4tb-nvme-ssd/) |
| Samsung 990 Pro | 4TB TLC | Amazon | new | **$799.99** | new | 2026-11-15 | reported (cheapestssd.com) | [link](https://cheapestssd.com/4tb-nvme-ssd/) |
| Crucial T500 | 4TB TLC | Amazon | new | **$869.00** | new | 2026-11-15 | reported (cheapestssd.com) | [link](https://cheapestssd.com/4tb-nvme-ssd/) |

<details>
<summary><b>SSDs: price history</b></summary>

##### Crucial T500 — Amazon (new)
Low $869.00 · High $869.00 · 1 entry

| Date | Price | Basis |
|---|--:|---|
| 2026-11-15 | [$869.00](https://cheapestssd.com/4tb-nvme-ssd/) | reported (cheapestssd.com) |

##### Samsung 990 EVO Plus — Amazon (new)
Low $679.99 · High $679.99 · 1 entry

| Date | Price | Basis |
|---|--:|---|
| 2026-11-15 | [$679.99](https://cheapestssd.com/4tb-nvme-ssd/) | reported (cheapestssd.com) |

##### Samsung 990 EVO Plus — B&H Photo (new)
Low $649.99 · High $649.99 · 3 entries

| Date | Price | Basis |
|---|--:|---|
| 2026-11-15 | [$649.99](https://9to5toys.com/2026/11/14/this-weeks-pc-deals-and-news/) | reported (9to5Toys) |
| 2026-11-14 | [$649.99](https://9to5toys.com/2026/11/14/this-weeks-pc-deals-and-news/) | reported (9to5Toys) |
| 2026-11-14 | [$649.99](https://9to5toys.com/2026/11/14/this-weeks-pc-deals-and-news/) | reported (9to5Toys) |

##### Samsung 990 Pro — Amazon (new)
Low $799.99 · High $799.99 · 1 entry

| Date | Price | Basis |
|---|--:|---|
| 2026-11-15 | [$799.99](https://cheapestssd.com/4tb-nvme-ssd/) | reported (cheapestssd.com) |

##### Silicon Power UD90 — Amazon (new)
Low $474.97 · High $529.97 · 3 entries

| Date | Price | Basis |
|---|--:|---|
| 2026-11-15 | [$529.97](https://cheapestssd.com/4tb-nvme-ssd/) | reported (cheapestssd.com) |
| 2026-11-14 | [$474.97](https://www.pcgamer.com/black-friday-ssd-deals/) | reported (PC Gamer) |
| 2026-11-14 | [$474.97](https://www.pcgamer.com/best-ssd-deals-today/) | reported (PC Gamer) |

##### Silicon Power UD90 — Newegg (new)
Low $475.00 · High $475.00 · 2 entries

| Date | Price | Basis |
|---|--:|---|
| 2026-11-15 | [$475.00](https://www.pcgamer.com/black-friday-ssd-deals/) | reported (PC Gamer) |
| 2026-11-14 | [$475.00](https://www.pcgamer.com/black-friday-ssd-deals/) | reported (PC Gamer) |

##### TeamGroup MP44 — Newegg (new)
Low $516.99 · High $516.99 · 2 entries

| Date | Price | Basis |
|---|--:|---|
| 2026-11-15 | [$516.99](https://www.pcgamer.com/black-friday-ssd-deals/) | reported (PC Gamer) |
| 2026-11-14 | [$516.99](https://www.pcgamer.com/black-friday-ssd-deals/) | reported (PC Gamer) |

##### TeamGroup MP44Q — Amazon (new)
Low $499.99 · High $499.99 · 3 entries

| Date | Price | Basis |
|---|--:|---|
| 2026-11-15 | [$499.99](https://www.pcgamer.com/black-friday-ssd-deals/) | reported (PC Gamer) |
| 2026-11-14 | [$499.99](https://www.pcgamer.com/black-friday-ssd-deals/) | reported (PC Gamer) |
| 2026-11-14 | [$499.99](https://www.pcgamer.com/best-ssd-deals-today/) | reported (PC Gamer) |

##### WD Black SN7100 — Amazon (new)
Low $629.99 · High $629.99 · 1 entry

| Date | Price | Basis |
|---|--:|---|
| 2026-11-15 | [$629.99](https://cheapestssd.com/4tb-nvme-ssd/) | reported (cheapestssd.com) |

##### WD Black SN850X — Amazon (new)
Low $784.99 · High $784.99 · 1 entry

| Date | Price | Basis |
|---|--:|---|
| 2026-11-15 | [$784.99](https://cheapestssd.com/4tb-nvme-ssd/) | reported (cheapestssd.com) |

##### WD Blue SN5000 — Newegg (new)
Low $491.00 · High $491.00 · 2 entries

| Date | Price | Basis |
|---|--:|---|
| 2026-11-15 | [$491.00](https://www.pcgamer.com/black-friday-ssd-deals/) | reported (PC Gamer) |
| 2026-11-14 | [$491.00](https://www.pcgamer.com/black-friday-ssd-deals/) | reported (PC Gamer) |

##### WD Blue SN5100 — Amazon (new)
Low $529.99 · High $529.99 · 1 entry

| Date | Price | Basis |
|---|--:|---|
| 2026-11-15 | [$529.99](https://cheapestssd.com/4tb-nvme-ssd/) | reported (cheapestssd.com) |

</details>

### NVIDIA GPUs

> **Cheapest new NVIDIA GPU on 2026-11-15:** RTX 5090 (ASUS TUF Gaming OC) (32GB GDDR7) at **$7,450.00** (Amazon) — [source](https://videocardprices.com/card/nvidia-rtx-5090/)

#### Cheapest by model

| Model | Cheapest new | Cheapest used / refurbished |
|---|---|---|
| RTX 5090 | [$7,450.00](https://videocardprices.com/card/nvidia-rtx-5090/) Amazon, 2026-11-15 | — |
| RTX 4090 | — | — |
| RTX 3090 Ti | — | — |
| RTX 3090 | — | [$1,799.22](https://camelcamelcamel.com/product/B08HR6ZBYJ) Amazon (third-party seller), 2026-11-14 |

<sub>Uses the most recent logged price for each item, store and condition.</sub>

#### Latest new price by model (cheapest store)

```mermaid
xychart-beta
    title "Most recent logged new price (USD)"
    x-axis ["RTX 5090"]
    y-axis "USD" 7440 --> 7460
    bar [7450.00]
```

<details>
<summary><b>New price over time, by model</b></summary>

#### RTX 5090: cheapest new price over time

```mermaid
xychart-beta
    title "Lowest new RTX 5090 price per day (USD)"
    x-axis ["11-14", "11-15"]
    y-axis "USD" 7440 --> 7460
    line [7450.00, 7450.00]
```

</details>

#### Latest prices

| Model | Item | Spec | Store | Condition | Price | Change | As of | Basis | Link |
|---|---|---|---|---|--:|--:|---|---|---|
| RTX 5090 | RTX 5090 (ASUS TUF Gaming OC) | 32GB GDDR7 | Amazon | new | **$7,450.00** | — | 2026-11-15 | reported (videocardprices.com) | [link](https://videocardprices.com/card/nvidia-rtx-5090/) |
| RTX 3090 | RTX 3090 (NVIDIA Founders Edition) | 24GB GDDR6X | Amazon (third-party seller) | used | **$1,799.22** | new | 2026-11-14 | reported (camelcamelcamel) | [link](https://camelcamelcamel.com/product/B08HR6ZBYJ) |

<details>
<summary><b>NVIDIA GPUs: price history</b></summary>

##### RTX 3090 (NVIDIA Founders Edition) — Amazon (third-party seller) (used)
Low $1,799.22 · High $1,799.22 · 1 entry

| Date | Price | Basis |
|---|--:|---|
| 2026-11-14 | [$1,799.22](https://camelcamelcamel.com/product/B08HR6ZBYJ) | reported (camelcamelcamel) |

##### RTX 5090 (ASUS TUF Gaming OC) — Amazon (new)
Low $7,450.00 · High $7,450.00 · 3 entries

| Date | Price | Basis |
|---|--:|---|
| 2026-11-15 | [$7,450.00](https://videocardprices.com/card/nvidia-rtx-5090/) | reported (videocardprices.com) |
| 2026-11-14 | [$7,450.00](https://videocardprices.com/card/nvidia-rtx-5090/) | reported (videocardprices.com) |
| 2026-11-14 | [$7,450.00](https://videocardprices.com/card/nvidia-rtx-5090/) | reported (videocardprices.com) |

</details>

### AMD GPUs

> **Cheapest new AMD GPU on 2026-11-15:** RX 9070 XT (GIGABYTE Gaming OC) (16GB GDDR6) at **$1,034.99** (Amazon) — [source](https://videocardprices.com/card/amd-rx-9070-xt/)

#### Cheapest by model

| Model | Cheapest new | Cheapest used / refurbished |
|---|---|---|
| RX 9070 XT | [$1,034.99](https://videocardprices.com/card/amd-rx-9070-xt/) Amazon, 2026-11-15 | — |
| RX 9070 | — | — |
| RX 7900 XTX | — | — |
| RX 7900 XT | — | — |

<sub>Uses the most recent logged price for each item, store and condition.</sub>

#### Latest new price by model (cheapest store)

```mermaid
xychart-beta
    title "Most recent logged new price (USD)"
    x-axis ["RX 9070 XT"]
    y-axis "USD" 1020 --> 1050
    bar [1034.99]
```

<details>
<summary><b>New price over time, by model</b></summary>

#### RX 9070 XT: cheapest new price over time

```mermaid
xychart-beta
    title "Lowest new RX 9070 XT price per day (USD)"
    x-axis ["11-15"]
    y-axis "USD" 1020 --> 1050
    line [1034.99]
    bar [1034.99]
```

</details>

#### Latest prices

| Model | Item | Spec | Store | Condition | Price | Change | As of | Basis | Link |
|---|---|---|---|---|--:|--:|---|---|---|
| RX 9070 XT | RX 9070 XT (GIGABYTE Gaming OC) | 16GB GDDR6 | Amazon | new | **$1,034.99** | new | 2026-11-15 | reported (videocardprices.com) | [link](https://videocardprices.com/card/amd-rx-9070-xt/) |

<details>
<summary><b>AMD GPUs: price history</b></summary>

##### RX 9070 XT (GIGABYTE Gaming OC) — Amazon (new)
Low $1,034.99 · High $1,034.99 · 1 entry

| Date | Price | Basis |
|---|--:|---|
| 2026-11-15 | [$1,034.99](https://videocardprices.com/card/amd-rx-9070-xt/) | reported (videocardprices.com) |

</details>

🔥 = DEAL: a new 4TB TLC SSD at $450.00 or less (SSDs only); or, in any category, a price at least 10% below the previous logged price for the same item, store and condition, or strictly below every earlier price for that item and condition once prices.csv has at least 7 days of history. Change is against the previous logged price for the same item, store and condition.

<sub>Generated from [`prices.csv`](prices.csv) by [`scripts/build_readme.py`](scripts/build_readme.py). Daily notes are in [`claude.md`](claude.md).</sub>
<!-- PRICES:END -->
