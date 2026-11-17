# Nitro V 16S Upgrade Price Watch

Daily US prices (USD) for upgrades and GPUs for an Acer Nitro V 16S (ANV16S-71), in five categories, plus high-memory MacBooks for comparison:

| Category | What's tracked |
|---|---|
| `ssd` | 4TB M.2 2280 NVMe PCIe 4.0 SSDs without a heatsink (Lexar NM790, TeamGroup MP44 and T-Force G50, WD Black SN7100 and SN850X, WD Blue SN5000, Samsung 990 EVO Plus and 990 Pro, Crucial T500 and P310, Kingston KC3000, Silicon Power UD90 and other reputable brands), plus the Micron 2500 |
| `ram` | Single 64GB DDR5 SO-DIMM modules, non-ECC, 5600 MT/s or faster |
| `nvidia_gpu` | Desktop RTX 5090, 4090, 3090 Ti and 3090, new and used/refurbished |
| `amd_gpu` | Desktop RX 9070 XT, 9070, 7900 XTX and 7900 XT (plus any newer Radeon above the 9070 XT), new and used/refurbished |
| `egpu` | Thunderbolt/USB4 eGPU enclosures and complete external GPUs |
| `macbook` | MacBook Pro and MacBook Air configurations with 48GB, 64GB, 96GB or 128GB of memory, new and used/refurbished |

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

[`scripts/track_gpus.py`](scripts/track_gpus.py) checks the RTX 5090, 4090, 3090 Ti and 3090 and the RX 9070 XT, 9070, 7900 XTX and 7900 XT on [videocardprices.com](https://videocardprices.com/). It also picks up any newer Radeon card numbered 9080 or higher. It logs in-stock Amazon, Newegg and eBay (used) prices of any age, with the date the source gives. The [Track GPU prices](.github/workflows/track-gpus.yml) Action runs it every day and rebuilds the dashboard.

```bash
python3 scripts/track_gpus.py            # dry run: show what would be logged
python3 scripts/track_gpus.py --write    # append new rows to prices.csv
```

videocardprices.com doesn't cover the RTX 4090, 3090 Ti, 3090 or RX 7900 XT, so the tracker reads those from [gpudeals.net](https://gpudeals.net/) instead. That site shows one Amazon and one eBay price per model, in whole dollars, with no board name or condition; the tracker logs the Amazon price as new and the eBay price as used under the bare model name. Log any other price by hand with [`scripts/add_price.py`](scripts/add_price.py). It applies the same rules:

```bash
python3 scripts/add_price.py nvidia_gpu "RTX 4090 (MSI Gaming X Trio)" "24GB GDDR6X" eBay used 1899.00 "https://www.ebay.com/itm/..."
```

### RAM price tracker

[`scripts/track_ram.py`](scripts/track_ram.py) checks single 64GB DDR5 SO-DIMM modules (1x64GB, 5600 MT/s) on their Amazon product pages: the Crucial CT64G56C46S5 and the G.Skill F5-5600S4645A64GX1-RS. It logs the in-stock price and marks the store as a third-party seller when Amazon isn't the seller. Add a module's Amazon ASIN and part number to `MODULES` in the script to track it.

```bash
python3 scripts/track_ram.py            # dry run: show what would be logged
python3 scripts/track_ram.py --write    # append new rows to prices.csv
```

Run the tests with `python3 -m unittest discover tests`.

## Dashboard

<!-- PRICES:START -->
**Last check:** 2026-11-17 &nbsp;·&nbsp; **Prices logged:** 104 &nbsp;·&nbsp; **Items tracked with prices:** 49 across 6 categories

> No DEAL flags on the latest check.

| Category | Latest-check rows | Cheapest new on latest check |
|---|--:|---|
| SSDs | 0 | — |
| RAM | 0 | — |
| NVIDIA GPUs | 0 | — |
| AMD GPUs | 0 | — |
| eGPUs | 0 | — |
| MacBooks | 16 | MacBook Pro 14 M5 Pro 48GB — $3,239.09 (Amazon (third-party seller)) |

### SSDs

> No new 4TB SSD price was found on 2026-11-17.

#### Cheapest new 4TB SSD price over time

```mermaid
xychart-beta
    title "Lowest new 4TB SSD price per day (USD)"
    x-axis ["11-14", "11-15", "11-16"]
    y-axis "USD" 460 --> 500
    line [474.97, 475.00, 484.99]
```

#### Latest price by item (new, cheapest store)

```mermaid
xychart-beta
    title "Most recent logged price (USD)"
    x-axis ["Silicon Power UD90", "TeamGroup MP44Q", "TeamGroup T-Force G50", "WD Blue SN5000", "TeamGroup MP44", "WD Blue SN5100", "Lexar NQ780", "WD Black SN7100", "Samsung 990 EVO Plus", "WD Black SN850X", "Samsung 990 Pro", "Crucial T500"]
    y-axis "USD" 410 --> 930
    bar [475.00, 484.99, 485.99, 491.00, 516.99, 599.99, 606.77, 629.99, 649.99, 784.99, 799.99, 869.00]
```

#### Latest prices

| Item | Spec | Store | Condition | Price | Change | As of | Basis | Link |
|---|---|---|---|--:|--:|---|---|---|
| Silicon Power UD90 | 4TB TLC (some batches reported QLC) | Newegg | new | **$475.00** | — | 2026-11-15 | reported (PC Gamer) | [link](https://www.pcgamer.com/black-friday-ssd-deals/) |
| TeamGroup MP44Q | 4TB QLC | Walmart (third-party seller) | new | **$484.99** | new | 2026-11-16 | reported (ByteSizedDeals) | [link](https://bytesizeddeals.com/ssd/4tb-pcie-4) |
| TeamGroup T-Force G50 | 4TB TLC | Walmart (third-party seller) | new | **$485.99** | new | 2026-11-15 | reported (ByteSizedDeals) | [link](https://bytesizeddeals.com/ssd/price-index) |
| WD Blue SN5000 | 4TB QLC | Newegg | new | **$491.00** | — | 2026-11-15 | reported (PC Gamer) | [link](https://www.pcgamer.com/black-friday-ssd-deals/) |
| TeamGroup T-Force G50 | 4TB TLC | Amazon (third-party seller) | new | **$495.99** | 🔺 $16.00 | 2026-11-16 | direct | [link](https://www.amazon.com/dp/B0DRVN1JXP) |
| TeamGroup T-Force G50 | 4TB TLC | Newegg | new | **$495.99** | new | 2026-11-16 | reported (ByteSizedDeals) | [link](https://bytesizeddeals.com/ssd/4tb-pcie-4) |
| TeamGroup MP44Q | 4TB QLC | Amazon | new | **$499.99** | — | 2026-11-15 | reported (PC Gamer) | [link](https://www.pcgamer.com/black-friday-ssd-deals/) |
| TeamGroup MP44 | 4TB TLC | Newegg | new | **$516.99** | — | 2026-11-15 | reported (PC Gamer) | [link](https://www.pcgamer.com/black-friday-ssd-deals/) |
| WD Blue SN5000 | 4TB QLC | Amazon (third-party seller) | new | **$519.95** | — | 2026-11-16 | direct | [link](https://www.amazon.com/dp/B0D7MLB76V) |
| Silicon Power UD90 | 4TB TLC (some batches reported QLC) | Amazon (third-party seller) | new | **$523.00** | — | 2026-11-16 | direct | [link](https://www.amazon.com/dp/B0BYN8NHXS) |
| Samsung 990 EVO Plus | 4TB TLC | Amazon (Amazon Resale) | used | **$525.36** | new | 2026-11-16 | direct | [link](https://www.amazon.com/dp/B0DHLBDSP7) |
| Silicon Power UD90 | 4TB TLC (some batches reported QLC) | Amazon | new | **$529.97** | 🔺 $55.00 | 2026-11-15 | reported (cheapestssd.com) | [link](https://cheapestssd.com/4tb-nvme-ssd/) |
| WD Blue SN5100 | 4TB QLC | Amazon | new | **$599.99** | 🔺 $70.00 | 2026-11-16 | direct | [link](https://www.amazon.com/dp/B0GJSJSDSM) |
| Lexar NQ780 | 4TB QLC | Amazon (third-party seller) | new | **$606.77** | 🔺 $37.10 | 2026-11-16 | direct | [link](https://www.amazon.com/dp/B0F25CX4LB) |
| WD Black SN7100 | 4TB TLC | Amazon | new | **$629.99** | new | 2026-11-15 | reported (cheapestssd.com) | [link](https://cheapestssd.com/4tb-nvme-ssd/) |
| WD Black SN7100 | 4TB TLC | Amazon (third-party seller) | new | **$629.99** | new | 2026-11-16 | direct | [link](https://www.amazon.com/dp/B0DZK9C789) |
| Samsung 990 EVO Plus | 4TB TLC | B&H Photo | new | **$649.99** | — | 2026-11-15 | reported (9to5Toys) | [link](https://9to5toys.com/2026/11/14/this-weeks-pc-deals-and-news/) |
| Samsung 990 EVO Plus | 4TB TLC | Amazon | new | **$679.99** | new | 2026-11-15 | reported (cheapestssd.com) | [link](https://cheapestssd.com/4tb-nvme-ssd/) |
| Samsung 990 EVO Plus | 4TB TLC | Amazon (third-party seller) | new | **$679.99** | new | 2026-11-16 | direct | [link](https://www.amazon.com/dp/B0DHLBDSP7) |
| WD Black SN850X | 4TB TLC | Amazon | new | **$784.99** | new | 2026-11-15 | reported (cheapestssd.com) | [link](https://cheapestssd.com/4tb-nvme-ssd/) |
| WD Black SN850X | 4TB TLC | Amazon (third-party seller) | new | **$789.99** | — | 2026-11-16 | direct | [link](https://www.amazon.com/dp/B0B7CQ2CHH) |
| Samsung 990 Pro | 4TB TLC | Amazon | new | **$799.99** | — | 2026-11-16 | direct | [link](https://www.amazon.com/dp/B0CHGT1KFJ) |
| Samsung 990 Pro | 4TB TLC | Best Buy | new | **$799.99** | new | 2026-11-16 | reported (ByteSizedDeals) | [link](https://bytesizeddeals.com/ssd/4tb-pcie-4) |
| Crucial T500 | 4TB TLC | Amazon | new | **$869.00** | new | 2026-11-15 | reported (cheapestssd.com) | [link](https://cheapestssd.com/4tb-nvme-ssd/) |
| Crucial T500 | 4TB TLC | Amazon (third-party seller) | new | **$869.00** | new | 2026-11-16 | direct | [link](https://www.amazon.com/dp/B0DBBG7CG7) |

<details>
<summary><b>SSDs: price history</b></summary>

##### Crucial T500 — Amazon (new)
Low $869.00 · High $869.00 · 1 entry

| Date | Price | Basis |
|---|--:|---|
| 2026-11-15 | [$869.00](https://cheapestssd.com/4tb-nvme-ssd/) | reported (cheapestssd.com) |

##### Crucial T500 — Amazon (third-party seller) (new)
Low $869.00 · High $869.00 · 1 entry

| Date | Price | Basis |
|---|--:|---|
| 2026-11-16 | [$869.00](https://www.amazon.com/dp/B0DBBG7CG7) | direct |

##### Lexar NQ780 — Amazon (third-party seller) (new)
Low $569.67 · High $606.77 · 2 entries

| Date | Price | Basis |
|---|--:|---|
| 2026-11-16 | [$606.77](https://www.amazon.com/dp/B0F25CX4LB) | direct |
| 2026-11-15 | [$569.67](https://www.amazon.com/dp/B0F25CX4LB) | direct |

##### Samsung 990 EVO Plus — Amazon (new)
Low $679.99 · High $679.99 · 1 entry

| Date | Price | Basis |
|---|--:|---|
| 2026-11-15 | [$679.99](https://cheapestssd.com/4tb-nvme-ssd/) | reported (cheapestssd.com) |

##### Samsung 990 EVO Plus — Amazon (Amazon Resale) (used)
Low $525.36 · High $525.36 · 1 entry

| Date | Price | Basis |
|---|--:|---|
| 2026-11-16 | [$525.36](https://www.amazon.com/dp/B0DHLBDSP7) | direct |

##### Samsung 990 EVO Plus — Amazon (third-party seller) (new)
Low $679.99 · High $679.99 · 1 entry

| Date | Price | Basis |
|---|--:|---|
| 2026-11-16 | [$679.99](https://www.amazon.com/dp/B0DHLBDSP7) | direct |

##### Samsung 990 EVO Plus — B&H Photo (new)
Low $649.99 · High $649.99 · 3 entries

| Date | Price | Basis |
|---|--:|---|
| 2026-11-15 | [$649.99](https://9to5toys.com/2026/11/14/this-weeks-pc-deals-and-news/) | reported (9to5Toys) |
| 2026-11-14 | [$649.99](https://9to5toys.com/2026/11/14/this-weeks-pc-deals-and-news/) | reported (9to5Toys) |
| 2026-11-14 | [$649.99](https://9to5toys.com/2026/11/14/this-weeks-pc-deals-and-news/) | reported (9to5Toys) |

##### Samsung 990 Pro — Amazon (new)
Low $799.99 · High $799.99 · 2 entries

| Date | Price | Basis |
|---|--:|---|
| 2026-11-16 | [$799.99](https://www.amazon.com/dp/B0CHGT1KFJ) | direct |
| 2026-11-15 | [$799.99](https://cheapestssd.com/4tb-nvme-ssd/) | reported (cheapestssd.com) |

##### Samsung 990 Pro — Best Buy (new)
Low $799.99 · High $799.99 · 1 entry

| Date | Price | Basis |
|---|--:|---|
| 2026-11-16 | [$799.99](https://bytesizeddeals.com/ssd/4tb-pcie-4) | reported (ByteSizedDeals) |

##### Silicon Power UD90 — Amazon (new)
Low $474.97 · High $529.97 · 3 entries

| Date | Price | Basis |
|---|--:|---|
| 2026-11-15 | [$529.97](https://cheapestssd.com/4tb-nvme-ssd/) | reported (cheapestssd.com) |
| 2026-11-14 | [$474.97](https://www.pcgamer.com/black-friday-ssd-deals/) | reported (PC Gamer) |
| 2026-11-14 | [$474.97](https://www.pcgamer.com/best-ssd-deals-today/) | reported (PC Gamer) |

##### Silicon Power UD90 — Amazon (third-party seller) (new)
Low $523.00 · High $523.00 · 2 entries

| Date | Price | Basis |
|---|--:|---|
| 2026-11-16 | [$523.00](https://www.amazon.com/dp/B0BYN8NHXS) | direct |
| 2026-11-15 | [$523.00](https://www.amazon.com/dp/B0BYN8NHXS) | direct |

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

##### TeamGroup MP44Q — Walmart (third-party seller) (new)
Low $484.99 · High $484.99 · 1 entry

| Date | Price | Basis |
|---|--:|---|
| 2026-11-16 | [$484.99](https://bytesizeddeals.com/ssd/4tb-pcie-4) | reported (ByteSizedDeals) |

##### TeamGroup T-Force G50 — Amazon (third-party seller) (new)
Low $479.99 · High $495.99 · 2 entries

| Date | Price | Basis |
|---|--:|---|
| 2026-11-16 | [$495.99](https://www.amazon.com/dp/B0DRVN1JXP) | direct |
| 2026-11-15 | [$479.99](https://www.amazon.com/dp/B0DRVN1JXP) | direct |

##### TeamGroup T-Force G50 — Newegg (new)
Low $495.99 · High $495.99 · 1 entry

| Date | Price | Basis |
|---|--:|---|
| 2026-11-16 | [$495.99](https://bytesizeddeals.com/ssd/4tb-pcie-4) | reported (ByteSizedDeals) |

##### TeamGroup T-Force G50 — Walmart (third-party seller) (new)
Low $485.99 · High $485.99 · 1 entry

| Date | Price | Basis |
|---|--:|---|
| 2026-11-15 | [$485.99](https://bytesizeddeals.com/ssd/price-index) | reported (ByteSizedDeals) |

##### WD Black SN7100 — Amazon (new)
Low $629.99 · High $629.99 · 1 entry

| Date | Price | Basis |
|---|--:|---|
| 2026-11-15 | [$629.99](https://cheapestssd.com/4tb-nvme-ssd/) | reported (cheapestssd.com) |

##### WD Black SN7100 — Amazon (third-party seller) (new)
Low $629.99 · High $629.99 · 1 entry

| Date | Price | Basis |
|---|--:|---|
| 2026-11-16 | [$629.99](https://www.amazon.com/dp/B0DZK9C789) | direct |

##### WD Black SN850X — Amazon (new)
Low $784.99 · High $784.99 · 1 entry

| Date | Price | Basis |
|---|--:|---|
| 2026-11-15 | [$784.99](https://cheapestssd.com/4tb-nvme-ssd/) | reported (cheapestssd.com) |

##### WD Black SN850X — Amazon (third-party seller) (new)
Low $789.99 · High $789.99 · 2 entries

| Date | Price | Basis |
|---|--:|---|
| 2026-11-16 | [$789.99](https://www.amazon.com/dp/B0B7CQ2CHH) | direct |
| 2026-11-15 | [$789.99](https://www.amazon.com/dp/B0B7CQ2CHH) | direct |

##### WD Blue SN5000 — Amazon (third-party seller) (new)
Low $519.95 · High $519.95 · 2 entries

| Date | Price | Basis |
|---|--:|---|
| 2026-11-16 | [$519.95](https://www.amazon.com/dp/B0D7MLB76V) | direct |
| 2026-11-15 | [$519.95](https://www.amazon.com/dp/B0D7MLB76V) | direct |

##### WD Blue SN5000 — Newegg (new)
Low $491.00 · High $491.00 · 2 entries

| Date | Price | Basis |
|---|--:|---|
| 2026-11-15 | [$491.00](https://www.pcgamer.com/black-friday-ssd-deals/) | reported (PC Gamer) |
| 2026-11-14 | [$491.00](https://www.pcgamer.com/black-friday-ssd-deals/) | reported (PC Gamer) |

##### WD Blue SN5100 — Amazon (new)
Low $529.99 · High $599.99 · 2 entries

| Date | Price | Basis |
|---|--:|---|
| 2026-11-16 | [$599.99](https://www.amazon.com/dp/B0GJSJSDSM) | direct |
| 2026-11-15 | [$529.99](https://cheapestssd.com/4tb-nvme-ssd/) | reported (cheapestssd.com) |

</details>

### RAM

> No new 64GB DDR5 SO-DIMM price was found on 2026-11-17.

#### Cheapest new 64GB DDR5 SO-DIMM price over time

```mermaid
xychart-beta
    title "Lowest new 64GB DDR5 SO-DIMM price per day (USD)"
    x-axis ["11-15", "11-16"]
    y-axis "USD" 1180 --> 1210
    line [1199.89, 1199.89]
```

#### Latest price by item (new, cheapest store)

```mermaid
xychart-beta
    title "Most recent logged price (USD)"
    x-axis ["Crucial CT64G56C46S5", "G.Skill F5-5600S4645A64GX1-RS"]
    y-axis "USD" 1070 --> 2130
    bar [1199.89, 1999.99]
```

#### Latest prices

| Item | Spec | Store | Condition | Price | Change | As of | Basis | Link |
|---|---|---|---|--:|--:|---|---|---|
| Crucial CT64G56C46S5 | 1x64GB DDR5-5600 CL46 | Amazon (third-party seller) | new | **$1,199.89** | — | 2026-11-16 | direct | [link](https://www.amazon.com/dp/B0DSQWZ5G2) |
| G.Skill F5-5600S4645A64GX1-RS | 1x64GB DDR5-5600 CL46 | Amazon (third-party seller) | new | **$1,999.99** | — | 2026-11-16 | direct | [link](https://www.amazon.com/dp/B0G7RLK95V) |

<details>
<summary><b>RAM: price history</b></summary>

##### Crucial CT64G56C46S5 — Amazon (third-party seller) (new)
Low $1,199.89 · High $1,199.89 · 2 entries

| Date | Price | Basis |
|---|--:|---|
| 2026-11-16 | [$1,199.89](https://www.amazon.com/dp/B0DSQWZ5G2) | direct |
| 2026-11-15 | [$1,199.89](https://www.amazon.com/dp/B0DSQWZ5G2) | direct |

##### G.Skill F5-5600S4645A64GX1-RS — Amazon (third-party seller) (new)
Low $1,999.99 · High $1,999.99 · 2 entries

| Date | Price | Basis |
|---|--:|---|
| 2026-11-16 | [$1,999.99](https://www.amazon.com/dp/B0G7RLK95V) | direct |
| 2026-11-15 | [$1,999.99](https://www.amazon.com/dp/B0G7RLK95V) | direct |

</details>

### NVIDIA GPUs

> No new NVIDIA GPU price was found on 2026-11-17.

#### Cheapest by model

| Model | Cheapest new | Cheapest used / refurbished |
|---|---|---|
| RTX 5090 | [$6,249.99](https://www.newegg.com/asus-rog-astral-rog-astral-rtx5090-o32g-gaming-geforce-rtx-5090-32gb-graphics-card-triple-fans/p/N82E16814126751?item=N82E16814126751) Newegg, 2026-11-15 | [$5,750.00](https://www.ebay.com/itm/407331778909) eBay, 2026-11-16 |
| RTX 4090 | [$5,500.00](https://www.amazon.com/dp/B0BJFRT43X) Amazon, 2026-11-16 | [$1,300.00](https://www.ebay.com/itm/366745135471) eBay, 2026-11-16 |
| RTX 3090 Ti | [$2,150.00](https://www.amazon.com/dp/B0BKH8HDWK) Amazon, 2026-11-16 | [$1,800.00](https://www.ebay.com/itm/820194234753) eBay, 2026-11-16 |
| RTX 3090 | [$2,450.00](https://www.amazon.com/dp/B09GWB753L) Amazon, 2026-11-16 | [$1,500.00](https://www.ebay.com/itm/287671509732) eBay, 2026-11-16 |

<sub>Uses the most recent logged price for each item, store and condition.</sub>

#### Latest new price by model (cheapest store)

```mermaid
xychart-beta
    title "Most recent logged new price (USD)"
    x-axis ["RTX 5090", "RTX 4090", "RTX 3090 Ti", "RTX 3090"]
    y-axis "USD" 1530 --> 6870
    bar [6249.99, 5500.00, 2150.00, 2450.00]
```

<details>
<summary><b>New price over time, by model</b></summary>

#### RTX 5090: cheapest new price over time

```mermaid
xychart-beta
    title "Lowest new RTX 5090 price per day (USD)"
    x-axis ["11-14", "11-15", "11-16"]
    y-axis "USD" 6060 --> 7640
    line [7450.00, 6249.99, 6599.99]
```

#### RTX 4090: cheapest new price over time

```mermaid
xychart-beta
    title "Lowest new RTX 4090 price per day (USD)"
    x-axis ["11-15", "11-16"]
    y-axis "USD" 5490 --> 5510
    line [5500.00, 5500.00]
```

#### RTX 3090 Ti: cheapest new price over time

```mermaid
xychart-beta
    title "Lowest new RTX 3090 Ti price per day (USD)"
    x-axis ["11-15", "11-16"]
    y-axis "USD" 2140 --> 2160
    line [2150.00, 2150.00]
```

#### RTX 3090: cheapest new price over time

```mermaid
xychart-beta
    title "Lowest new RTX 3090 price per day (USD)"
    x-axis ["11-15", "11-16"]
    y-axis "USD" 2440 --> 2460
    line [2450.00, 2450.00]
```

</details>

#### Latest prices

| Model | Item | Spec | Store | Condition | Price | Change | As of | Basis | Link |
|---|---|---|---|---|--:|--:|---|---|---|
| RTX 5090 | RTX 5090 (Gigabyte Gaming OC) | 32GB GDDR7 | eBay | used | **$5,750.00** | new | 2026-11-16 | reported (videocardprices.com) | [link](https://www.ebay.com/itm/407331778909) |
| RTX 5090 | RTX 5090 (ASUS ROG Astral OC) | 32GB GDDR7 | eBay | used | **$5,999.00** | new | 2026-11-15 | reported (videocardprices.com) | [link](https://www.ebay.com/itm/880090793238) |
| RTX 5090 | RTX 5090 (ASUS ROG Astral OC) | 32GB GDDR7 | Newegg | new | **$6,249.99** | new | 2026-11-15 | reported (videocardprices.com) | [link](https://www.newegg.com/asus-rog-astral-rog-astral-rtx5090-o32g-gaming-geforce-rtx-5090-32gb-graphics-card-triple-fans/p/N82E16814126751?item=N82E16814126751) |
| RTX 5090 | RTX 5090 (GIGABYTE AORUS) | 32GB GDDR7 | Newegg | new | **$6,599.99** | new | 2026-11-16 | reported (videocardprices.com) | [link](https://www.newegg.com/gigabyte-gv-n5090aorusx-w-32gd-geforce-rtx-5090-32gb-graphics-card/p/N82E16814932763?item=N82E16814932763) |
| RTX 5090 | RTX 5090 (ASUS TUF Gaming OC) | 32GB GDDR7 | Amazon | new | **$7,450.00** | — | 2026-11-16 | reported (videocardprices.com) | [link](https://www.amazon.com/dp/B0DS2X13PH) |
| RTX 4090 | RTX 4090 | 24GB GDDR6X | eBay | used | **$1,300.00** | — | 2026-11-16 | reported (gpudeals.net) | [link](https://www.ebay.com/itm/366745135471) |
| RTX 4090 | RTX 4090 | 24GB GDDR6X | Amazon | new | **$5,500.00** | — | 2026-11-16 | reported (gpudeals.net) | [link](https://www.amazon.com/dp/B0BJFRT43X) |
| RTX 3090 Ti | RTX 3090 Ti | 24GB GDDR6X | eBay | used | **$1,800.00** | 🔻 $95.00 | 2026-11-16 | reported (gpudeals.net) | [link](https://www.ebay.com/itm/820194234753) |
| RTX 3090 Ti | RTX 3090 Ti | 24GB GDDR6X | Amazon | new | **$2,150.00** | — | 2026-11-16 | reported (gpudeals.net) | [link](https://www.amazon.com/dp/B0BKH8HDWK) |
| RTX 3090 | RTX 3090 | 24GB GDDR6X | eBay | used | **$1,500.00** | — | 2026-11-16 | reported (gpudeals.net) | [link](https://www.ebay.com/itm/287671509732) |
| RTX 3090 | RTX 3090 (NVIDIA Founders Edition) | 24GB GDDR6X | Amazon (third-party seller) | used | **$1,799.22** | new | 2026-11-14 | reported (camelcamelcamel) | [link](https://camelcamelcamel.com/product/B08HR6ZBYJ) |
| RTX 3090 | RTX 3090 | 24GB GDDR6X | Amazon | new | **$2,450.00** | — | 2026-11-16 | reported (gpudeals.net) | [link](https://www.amazon.com/dp/B09GWB753L) |

<details>
<summary><b>NVIDIA GPUs: price history</b></summary>

##### RTX 3090 — Amazon (new)
Low $2,450.00 · High $2,450.00 · 2 entries

| Date | Price | Basis |
|---|--:|---|
| 2026-11-16 | [$2,450.00](https://www.amazon.com/dp/B09GWB753L) | reported (gpudeals.net) |
| 2026-11-15 | [$2,450.00](https://www.amazon.com/dp/B09GWB753L) | reported (gpudeals.net) |

##### RTX 3090 — eBay (used)
Low $1,500.00 · High $1,500.00 · 2 entries

| Date | Price | Basis |
|---|--:|---|
| 2026-11-16 | [$1,500.00](https://www.ebay.com/itm/287671509732) | reported (gpudeals.net) |
| 2026-11-15 | [$1,500.00](https://www.ebay.com/itm/287671509732) | reported (gpudeals.net) |

##### RTX 3090 (NVIDIA Founders Edition) — Amazon (third-party seller) (used)
Low $1,799.22 · High $1,799.22 · 1 entry

| Date | Price | Basis |
|---|--:|---|
| 2026-11-14 | [$1,799.22](https://camelcamelcamel.com/product/B08HR6ZBYJ) | reported (camelcamelcamel) |

##### RTX 3090 Ti — Amazon (new)
Low $2,150.00 · High $2,150.00 · 2 entries

| Date | Price | Basis |
|---|--:|---|
| 2026-11-16 | [$2,150.00](https://www.amazon.com/dp/B0BKH8HDWK) | reported (gpudeals.net) |
| 2026-11-15 | [$2,150.00](https://www.amazon.com/dp/B0BKH8HDWK) | reported (gpudeals.net) |

##### RTX 3090 Ti — eBay (used)
Low $1,800.00 · High $1,895.00 · 2 entries

| Date | Price | Basis |
|---|--:|---|
| 2026-11-16 | [$1,800.00](https://www.ebay.com/itm/820194234753) | reported (gpudeals.net) |
| 2026-11-15 | [$1,895.00](https://www.ebay.com/itm/366810925420) | reported (gpudeals.net) |

##### RTX 4090 — Amazon (new)
Low $5,500.00 · High $5,500.00 · 2 entries

| Date | Price | Basis |
|---|--:|---|
| 2026-11-16 | [$5,500.00](https://www.amazon.com/dp/B0BJFRT43X) | reported (gpudeals.net) |
| 2026-11-15 | [$5,500.00](https://www.amazon.com/dp/B0BJFRT43X) | reported (gpudeals.net) |

##### RTX 4090 — eBay (used)
Low $1,300.00 · High $1,300.00 · 2 entries

| Date | Price | Basis |
|---|--:|---|
| 2026-11-16 | [$1,300.00](https://www.ebay.com/itm/366745135471) | reported (gpudeals.net) |
| 2026-11-15 | [$1,300.00](https://www.ebay.com/itm/366745135471) | reported (gpudeals.net) |

##### RTX 5090 (ASUS ROG Astral OC) — Newegg (new)
Low $6,249.99 · High $6,249.99 · 1 entry

| Date | Price | Basis |
|---|--:|---|
| 2026-11-15 | [$6,249.99](https://www.newegg.com/asus-rog-astral-rog-astral-rtx5090-o32g-gaming-geforce-rtx-5090-32gb-graphics-card-triple-fans/p/N82E16814126751?item=N82E16814126751) | reported (videocardprices.com) |

##### RTX 5090 (ASUS ROG Astral OC) — eBay (used)
Low $5,999.00 · High $5,999.00 · 1 entry

| Date | Price | Basis |
|---|--:|---|
| 2026-11-15 | [$5,999.00](https://www.ebay.com/itm/880090793238) | reported (videocardprices.com) |

##### RTX 5090 (ASUS TUF Gaming OC) — Amazon (new)
Low $7,450.00 · High $7,450.00 · 4 entries

| Date | Price | Basis |
|---|--:|---|
| 2026-11-16 | [$7,450.00](https://www.amazon.com/dp/B0DS2X13PH) | reported (videocardprices.com) |
| 2026-11-15 | [$7,450.00](https://videocardprices.com/card/nvidia-rtx-5090/) | reported (videocardprices.com) |
| 2026-11-14 | [$7,450.00](https://videocardprices.com/card/nvidia-rtx-5090/) | reported (videocardprices.com) |
| 2026-11-14 | [$7,450.00](https://videocardprices.com/card/nvidia-rtx-5090/) | reported (videocardprices.com) |

##### RTX 5090 (GIGABYTE AORUS) — Newegg (new)
Low $6,599.99 · High $6,599.99 · 1 entry

| Date | Price | Basis |
|---|--:|---|
| 2026-11-16 | [$6,599.99](https://www.newegg.com/gigabyte-gv-n5090aorusx-w-32gd-geforce-rtx-5090-32gb-graphics-card/p/N82E16814932763?item=N82E16814932763) | reported (videocardprices.com) |

##### RTX 5090 (Gigabyte Gaming OC) — eBay (used)
Low $5,750.00 · High $5,750.00 · 1 entry

| Date | Price | Basis |
|---|--:|---|
| 2026-11-16 | [$5,750.00](https://www.ebay.com/itm/407331778909) | reported (videocardprices.com) |

</details>

### AMD GPUs

> No new AMD GPU price was found on 2026-11-17.

#### Cheapest by model

| Model | Cheapest new | Cheapest used / refurbished |
|---|---|---|
| RX 9070 XT | [$949.99](https://www.newegg.com/asrock-challenger-rx9070xt-cl-16g-radeon-rx-9070-xt-16gb-graphics-card-triple-fans/p/N82E16814930145?item=N82E16814930145) Newegg, 2026-11-16 | [$899.00](https://www.ebay.com/itm/168853292500) eBay, 2026-11-15 |
| RX 9070 | [$879.99](https://www.amazon.com/dp/B0DXLBTL4B) Amazon, 2026-11-16 | [$830.00](https://www.ebay.com/itm/267843983228) eBay, 2026-11-16 |
| RX 7900 XTX | [$1,099.99](https://www.amazon.com/dp/B0BTPK5J68) Amazon, 2026-11-16 | — |
| RX 7900 XT | [$946.00](https://www.amazon.com/dp/B0BMNGT8XM) Amazon, 2026-11-16 | [$900.00](https://www.ebay.com/itm/960194484387) eBay, 2026-11-16 |

<sub>Uses the most recent logged price for each item, store and condition.</sub>

#### Latest new price by model (cheapest store)

```mermaid
xychart-beta
    title "Most recent logged new price (USD)"
    x-axis ["RX 9070 XT", "RX 9070", "RX 7900 XTX", "RX 7900 XT"]
    y-axis "USD" 840 --> 1140
    bar [949.99, 879.99, 1099.99, 946.00]
```

<details>
<summary><b>New price over time, by model</b></summary>

#### RX 9070 XT: cheapest new price over time

```mermaid
xychart-beta
    title "Lowest new RX 9070 XT price per day (USD)"
    x-axis ["11-15", "11-16"]
    y-axis "USD" 930 --> 960
    line [949.99, 949.99]
```

#### RX 9070: cheapest new price over time

```mermaid
xychart-beta
    title "Lowest new RX 9070 price per day (USD)"
    x-axis ["11-15", "11-16"]
    y-axis "USD" 860 --> 890
    line [879.99, 879.99]
```

#### RX 7900 XTX: cheapest new price over time

```mermaid
xychart-beta
    title "Lowest new RX 7900 XTX price per day (USD)"
    x-axis ["11-15", "11-16"]
    y-axis "USD" 1080 --> 1110
    line [1099.99, 1099.99]
```

#### RX 7900 XT: cheapest new price over time

```mermaid
xychart-beta
    title "Lowest new RX 7900 XT price per day (USD)"
    x-axis ["11-15", "11-16"]
    y-axis "USD" 930 --> 960
    line [946.00, 946.00]
```

</details>

#### Latest prices

| Model | Item | Spec | Store | Condition | Price | Change | As of | Basis | Link |
|---|---|---|---|---|--:|--:|---|---|---|
| RX 9070 XT | RX 9070 XT (PowerColor OC) | 16GB GDDR6 | eBay | used | **$899.00** | new | 2026-11-15 | reported (videocardprices.com) | [link](https://www.ebay.com/itm/168853292500) |
| RX 9070 XT | RX 9070 XT (XFX Gaming) | 16GB GDDR6 | eBay | used | **$929.97** | new | 2026-11-16 | reported (videocardprices.com) | [link](https://www.ebay.com/itm/117519818319) |
| RX 9070 XT | RX 9070 XT (ASRock Challenger) | 16GB GDDR6 | Newegg | new | **$949.99** | — | 2026-11-16 | reported (videocardprices.com) | [link](https://www.newegg.com/asrock-challenger-rx9070xt-cl-16g-radeon-rx-9070-xt-16gb-graphics-card-triple-fans/p/N82E16814930145?item=N82E16814930145) |
| RX 9070 XT | RX 9070 XT (GIGABYTE Gaming OC) | 16GB GDDR6 | Amazon | new | **$1,034.99** | — | 2026-11-16 | reported (videocardprices.com) | [link](https://www.amazon.com/dp/B0DS2QG2KW) |
| RX 9070 | RX 9070 (AsRock Challenger) | 16GB GDDR6 | eBay | used | **$830.00** | new | 2026-11-16 | reported (videocardprices.com) | [link](https://www.ebay.com/itm/267843983228) |
| RX 9070 | RX 9070 (ASRock Steel Legend) | 16GB GDDR6 | eBay | used | **$848.99** | new | 2026-11-15 | reported (videocardprices.com) | [link](https://www.ebay.com/itm/327453479284) |
| RX 9070 | RX 9070 (XFX Swift OC Triple Fan) | 16GB GDDR6 | Amazon | new | **$879.99** | — | 2026-11-16 | reported (videocardprices.com) | [link](https://www.amazon.com/dp/B0DXLBTL4B) |
| RX 9070 | RX 9070 (GIGABYTE Gaming) | 16GB GDDR6 | Newegg | new | **$934.99** | — | 2026-11-16 | reported (videocardprices.com) | [link](https://www.newegg.com/gigabyte-gv-r9070gaming-oc-16gd-radeon-rx-9070-16gb-graphics-card-triple-fans/p/N82E16814932752?item=N82E16814932752) |
| RX 7900 XTX | RX 7900 XTX (ASRock Phantom Gaming OC) | 24GB GDDR6 | Amazon | new | **$1,099.99** | — | 2026-11-16 | reported (videocardprices.com) | [link](https://www.amazon.com/dp/B0BTPK5J68) |
| RX 7900 XT | RX 7900 XT | 20GB GDDR6 | eBay | used | **$900.00** | — | 2026-11-16 | reported (gpudeals.net) | [link](https://www.ebay.com/itm/960194484387) |
| RX 7900 XT | RX 7900 XT | 20GB GDDR6 | Amazon | new | **$946.00** | — | 2026-11-16 | reported (gpudeals.net) | [link](https://www.amazon.com/dp/B0BMNGT8XM) |

<details>
<summary><b>AMD GPUs: price history</b></summary>

##### RX 7900 XT — Amazon (new)
Low $946.00 · High $946.00 · 2 entries

| Date | Price | Basis |
|---|--:|---|
| 2026-11-16 | [$946.00](https://www.amazon.com/dp/B0BMNGT8XM) | reported (gpudeals.net) |
| 2026-11-15 | [$946.00](https://www.amazon.com/dp/B0BMNGT8XM) | reported (gpudeals.net) |

##### RX 7900 XT — eBay (used)
Low $900.00 · High $900.00 · 2 entries

| Date | Price | Basis |
|---|--:|---|
| 2026-11-16 | [$900.00](https://www.ebay.com/itm/960194484387) | reported (gpudeals.net) |
| 2026-11-15 | [$900.00](https://www.ebay.com/itm/960194484387) | reported (gpudeals.net) |

##### RX 7900 XTX (ASRock Phantom Gaming OC) — Amazon (new)
Low $1,099.99 · High $1,099.99 · 2 entries

| Date | Price | Basis |
|---|--:|---|
| 2026-11-16 | [$1,099.99](https://www.amazon.com/dp/B0BTPK5J68) | reported (videocardprices.com) |
| 2026-11-15 | [$1,099.99](https://www.amazon.com/dp/B0BTPK5J68) | reported (videocardprices.com) |

##### RX 9070 (ASRock Steel Legend) — eBay (used)
Low $848.99 · High $848.99 · 1 entry

| Date | Price | Basis |
|---|--:|---|
| 2026-11-15 | [$848.99](https://www.ebay.com/itm/327453479284) | reported (videocardprices.com) |

##### RX 9070 (AsRock Challenger) — eBay (used)
Low $830.00 · High $830.00 · 1 entry

| Date | Price | Basis |
|---|--:|---|
| 2026-11-16 | [$830.00](https://www.ebay.com/itm/267843983228) | reported (videocardprices.com) |

##### RX 9070 (GIGABYTE Gaming) — Newegg (new)
Low $934.99 · High $934.99 · 2 entries

| Date | Price | Basis |
|---|--:|---|
| 2026-11-16 | [$934.99](https://www.newegg.com/gigabyte-gv-r9070gaming-oc-16gd-radeon-rx-9070-16gb-graphics-card-triple-fans/p/N82E16814932752?item=N82E16814932752) | reported (videocardprices.com) |
| 2026-11-15 | [$934.99](https://www.newegg.com/gigabyte-gv-r9070gaming-oc-16gd-radeon-rx-9070-16gb-graphics-card-triple-fans/p/N82E16814932752?item=N82E16814932752) | reported (videocardprices.com) |

##### RX 9070 (XFX Swift OC Triple Fan) — Amazon (new)
Low $879.99 · High $879.99 · 2 entries

| Date | Price | Basis |
|---|--:|---|
| 2026-11-16 | [$879.99](https://www.amazon.com/dp/B0DXLBTL4B) | reported (videocardprices.com) |
| 2026-11-15 | [$879.99](https://www.amazon.com/dp/B0DXLBTL4B) | reported (videocardprices.com) |

##### RX 9070 XT (ASRock Challenger) — Newegg (new)
Low $949.99 · High $949.99 · 2 entries

| Date | Price | Basis |
|---|--:|---|
| 2026-11-16 | [$949.99](https://www.newegg.com/asrock-challenger-rx9070xt-cl-16g-radeon-rx-9070-xt-16gb-graphics-card-triple-fans/p/N82E16814930145?item=N82E16814930145) | reported (videocardprices.com) |
| 2026-11-15 | [$949.99](https://www.newegg.com/asrock-challenger-rx9070xt-cl-16g-radeon-rx-9070-xt-16gb-graphics-card-triple-fans/p/N82E16814930145?item=N82E16814930145) | reported (videocardprices.com) |

##### RX 9070 XT (GIGABYTE Gaming OC) — Amazon (new)
Low $1,034.99 · High $1,034.99 · 2 entries

| Date | Price | Basis |
|---|--:|---|
| 2026-11-16 | [$1,034.99](https://www.amazon.com/dp/B0DS2QG2KW) | reported (videocardprices.com) |
| 2026-11-15 | [$1,034.99](https://videocardprices.com/card/amd-rx-9070-xt/) | reported (videocardprices.com) |

##### RX 9070 XT (PowerColor OC) — eBay (used)
Low $899.00 · High $899.00 · 1 entry

| Date | Price | Basis |
|---|--:|---|
| 2026-11-15 | [$899.00](https://www.ebay.com/itm/168853292500) | reported (videocardprices.com) |

##### RX 9070 XT (XFX Gaming) — eBay (used)
Low $929.97 · High $929.97 · 1 entry

| Date | Price | Basis |
|---|--:|---|
| 2026-11-16 | [$929.97](https://www.ebay.com/itm/117519818319) | reported (videocardprices.com) |

</details>

### eGPUs

> No new eGPU price was found on 2026-11-17.

#### Cheapest new eGPU price over time

```mermaid
xychart-beta
    title "Lowest new eGPU price per day (USD)"
    x-axis ["11-15", "11-16"]
    y-axis "USD" 200 --> 230
    line [219.00, 219.00]
```

#### Latest price by item (new, cheapest store)

```mermaid
xychart-beta
    title "Most recent logged price (USD)"
    x-axis ["AOOSTAR EG02", "Razer Core X V2"]
    y-axis "USD" 190 --> 370
    bar [219.00, 349.99]
```

#### Latest prices

| Item | Spec | Store | Condition | Price | Change | As of | Basis | Link |
|---|---|---|---|--:|--:|---|---|---|
| AOOSTAR EG02 | Enclosure, TB5, No PSU / ATX required | Amazon (third-party seller) | new | **$219.00** | — | 2026-11-16 | direct | [link](https://www.amazon.com/dp/B0G3TV5HKJ) |
| Razer Core X V2 | Enclosure, TB5, No PSU | Amazon | new | **$349.99** | — | 2026-11-16 | direct | [link](https://www.amazon.com/dp/B0FFQFDZWX) |

<details>
<summary><b>eGPUs: price history</b></summary>

##### AOOSTAR EG02 — Amazon (third-party seller) (new)
Low $219.00 · High $219.00 · 2 entries

| Date | Price | Basis |
|---|--:|---|
| 2026-11-16 | [$219.00](https://www.amazon.com/dp/B0G3TV5HKJ) | direct |
| 2026-11-15 | [$219.00](https://www.amazon.com/dp/B0G3TV5HKJ) | direct |

##### Razer Core X V2 — Amazon (new)
Low $349.99 · High $349.99 · 2 entries

| Date | Price | Basis |
|---|--:|---|
| 2026-11-16 | [$349.99](https://www.amazon.com/dp/B0FFQFDZWX) | direct |
| 2026-11-15 | [$349.99](https://www.amazon.com/dp/B0FFQFDZWX) | direct |

</details>

### MacBooks

> **Cheapest new high-memory MacBook on 2026-11-17:** MacBook Pro 14 M5 Pro 48GB (48GB RAM, 1TB SSD, 15C CPU/16C GPU) at **$3,239.09** (Amazon (third-party seller)) — [source](https://www.amazon.com/dp/B0H46QQ5KM)

#### Cheapest new high-memory MacBook price over time

```mermaid
xychart-beta
    title "Lowest new high-memory MacBook price per day (USD)"
    x-axis ["11-17"]
    y-axis "USD" 3220 --> 3250
    line [3239.09]
    bar [3239.09]
```

#### Latest price by item (new, cheapest store)

```mermaid
xychart-beta
    title "Most recent logged price (USD)"
    x-axis ["MacBook Pro 14 M5 Pro 48GB", "MacBook Pro 14 M5 Pro 64GB", "MacBook Pro 16 M5 Max 48GB", "MacBook Pro 16 M5 Pro 64GB", "MacBook Pro 14 M5 Max 64GB", "MacBook Pro 14 M5 Max 128GB", "MacBook Pro 16 M5 Max 128GB"]
    y-axis "USD" 2670 --> 7570
    bar [3239.09, 3699.00, 4499.00, 4599.00, 5099.00, 6699.00, 6999.00]
```

#### Latest prices

| Item | Spec | Store | Condition | Price | Change | As of | Basis | Link |
|---|---|---|---|--:|--:|---|---|---|
| MacBook Pro 16 M1 Max 64GB | 64GB RAM, 1TB SSD | Amazon (third-party seller) | refurbished | **$1,654.00** | new | 2026-11-17 | direct | [link](https://www.amazon.com/dp/B0CLJTSXHF) |
| MacBook Pro 14 M1 Max 64GB | 64GB RAM, 2TB SSD | Amazon (third-party seller) | refurbished | **$1,779.99** | new | 2026-11-17 | direct | [link](https://www.amazon.com/dp/B0F8JNXBY4) |
| MacBook Pro 16 M4 Pro 48GB | 48GB RAM, 512GB SSD, 14C CPU/20C GPU | Amazon (third-party seller) | refurbished | **$2,199.00** | new | 2026-11-17 | direct | [link](https://www.amazon.com/dp/B0FT4PJ9QP) |
| MacBook Pro 16 M2 Max 64GB | 64GB RAM, 1TB SSD | Amazon (third-party seller) | refurbished | **$2,488.80** | new | 2026-11-17 | direct | [link](https://www.amazon.com/dp/B0FHP6C3BL) |
| MacBook Pro 16 M5 Pro 48GB | 48GB RAM, 1TB SSD, 18C CPU/20C GPU | Apple (Certified Refurbished) | refurbished | **$3,059.00** | new | 2026-11-17 | direct | [link](https://www.apple.com/shop/product/fgec4ll/a/Refurbished-16-inch-MacBook-Pro-Apple-M5-Pro-chip-with-18%E2%80%91Core-CPU-and-20%E2%80%91Core-GPU-Space-Black) |
| MacBook Pro 16 M3 Max 64GB | 64GB RAM, 1TB SSD, 16C CPU/40C GPU | Amazon (third-party seller) | refurbished | **$3,199.00** | new | 2026-11-17 | direct | [link](https://www.amazon.com/dp/B0F1Z7BR77) |
| MacBook Pro 14 M5 Pro 48GB | 48GB RAM, 1TB SSD, 15C CPU/16C GPU | Amazon (third-party seller) | new | **$3,239.09** | new | 2026-11-17 | direct | [link](https://www.amazon.com/dp/B0H46QQ5KM) |
| MacBook Pro 14 M4 Pro 48GB | 48GB RAM, 2TB SSD, 14C CPU/20C GPU | Apple (Certified Refurbished) | refurbished | **$3,269.00** | new | 2026-11-17 | direct | [link](https://www.apple.com/shop/product/g1ff9ll/a/Refurbished-14-inch-MacBook-Pro-Apple-M4-Pro-Chip-with-14%E2%80%91Core-CPU-and-20%E2%80%91Core-GPU-Nano-texture-display-Space-Black) |
| MacBook Pro 16 M4 Max 48GB | 48GB RAM, 1TB SSD | Amazon (third-party seller) | refurbished | **$3,272.00** | new | 2026-11-17 | direct | [link](https://www.amazon.com/dp/B0DN25LGK8) |
| MacBook Pro 14 M5 Pro 64GB | 64GB RAM, 1TB SSD, 18C CPU/20C GPU | Amazon (third-party seller) | new | **$3,699.00** | new | 2026-11-17 | direct | [link](https://www.amazon.com/dp/B0GYZKZ2WX) |
| MacBook Pro 16 M5 Max 48GB | 48GB RAM, 2TB SSD, 18C CPU/40C GPU | Apple (Certified Refurbished) | refurbished | **$4,249.00** | new | 2026-11-17 | direct | [link](https://www.apple.com/shop/product/fge94ll/a/Refurbished-16-inch-MacBook-Pro-Apple-M5-Max-chip-with-18%E2%80%91Core-CPU-and-40%E2%80%91Core-GPU-Silver) |
| MacBook Pro 16 M5 Max 48GB | 48GB RAM, 2TB SSD, 18C CPU/40C GPU | Amazon | new | **$4,499.00** | new | 2026-11-17 | direct | [link](https://www.amazon.com/dp/B0GR1G6V6H) |
| MacBook Pro 16 M5 Pro 64GB | 64GB RAM, 1TB SSD, 18C CPU/20C GPU | Amazon (third-party seller) | new | **$4,599.00** | new | 2026-11-17 | direct | [link](https://www.amazon.com/dp/B0H7Z68CLL) |
| MacBook Pro 14 M5 Max 64GB | 64GB RAM, 2TB SSD, 18C CPU/40C GPU | Amazon (third-party seller) | new | **$5,099.00** | new | 2026-11-17 | direct | [link](https://www.amazon.com/dp/B0GWS9J8KY) |
| MacBook Pro 14 M5 Max 128GB | 128GB RAM, 2TB SSD, 18C CPU/40C GPU | Amazon (third-party seller) | new | **$6,699.00** | new | 2026-11-17 | direct | [link](https://www.amazon.com/dp/B0GZ4SQXGD) |
| MacBook Pro 16 M5 Max 128GB | 128GB RAM, 2TB SSD, 18C CPU/40C GPU | Amazon (third-party seller) | new | **$6,999.00** | new | 2026-11-17 | direct | [link](https://www.amazon.com/dp/B0GYZYQC19) |

<details>
<summary><b>MacBooks: price history</b></summary>

##### MacBook Pro 14 M1 Max 64GB — Amazon (third-party seller) (refurbished)
Low $1,779.99 · High $1,779.99 · 1 entry

| Date | Price | Basis |
|---|--:|---|
| 2026-11-17 | [$1,779.99](https://www.amazon.com/dp/B0F8JNXBY4) | direct |

##### MacBook Pro 14 M4 Pro 48GB — Apple (Certified Refurbished) (refurbished)
Low $3,269.00 · High $3,269.00 · 1 entry

| Date | Price | Basis |
|---|--:|---|
| 2026-11-17 | [$3,269.00](https://www.apple.com/shop/product/g1ff9ll/a/Refurbished-14-inch-MacBook-Pro-Apple-M4-Pro-Chip-with-14%E2%80%91Core-CPU-and-20%E2%80%91Core-GPU-Nano-texture-display-Space-Black) | direct |

##### MacBook Pro 14 M5 Max 128GB — Amazon (third-party seller) (new)
Low $6,699.00 · High $6,699.00 · 1 entry

| Date | Price | Basis |
|---|--:|---|
| 2026-11-17 | [$6,699.00](https://www.amazon.com/dp/B0GZ4SQXGD) | direct |

##### MacBook Pro 14 M5 Max 64GB — Amazon (third-party seller) (new)
Low $5,099.00 · High $5,099.00 · 1 entry

| Date | Price | Basis |
|---|--:|---|
| 2026-11-17 | [$5,099.00](https://www.amazon.com/dp/B0GWS9J8KY) | direct |

##### MacBook Pro 14 M5 Pro 48GB — Amazon (third-party seller) (new)
Low $3,239.09 · High $3,239.09 · 1 entry

| Date | Price | Basis |
|---|--:|---|
| 2026-11-17 | [$3,239.09](https://www.amazon.com/dp/B0H46QQ5KM) | direct |

##### MacBook Pro 14 M5 Pro 64GB — Amazon (third-party seller) (new)
Low $3,699.00 · High $3,699.00 · 1 entry

| Date | Price | Basis |
|---|--:|---|
| 2026-11-17 | [$3,699.00](https://www.amazon.com/dp/B0GYZKZ2WX) | direct |

##### MacBook Pro 16 M1 Max 64GB — Amazon (third-party seller) (refurbished)
Low $1,654.00 · High $1,654.00 · 1 entry

| Date | Price | Basis |
|---|--:|---|
| 2026-11-17 | [$1,654.00](https://www.amazon.com/dp/B0CLJTSXHF) | direct |

##### MacBook Pro 16 M2 Max 64GB — Amazon (third-party seller) (refurbished)
Low $2,488.80 · High $2,488.80 · 1 entry

| Date | Price | Basis |
|---|--:|---|
| 2026-11-17 | [$2,488.80](https://www.amazon.com/dp/B0FHP6C3BL) | direct |

##### MacBook Pro 16 M3 Max 64GB — Amazon (third-party seller) (refurbished)
Low $3,199.00 · High $3,199.00 · 1 entry

| Date | Price | Basis |
|---|--:|---|
| 2026-11-17 | [$3,199.00](https://www.amazon.com/dp/B0F1Z7BR77) | direct |

##### MacBook Pro 16 M4 Max 48GB — Amazon (third-party seller) (refurbished)
Low $3,272.00 · High $3,272.00 · 1 entry

| Date | Price | Basis |
|---|--:|---|
| 2026-11-17 | [$3,272.00](https://www.amazon.com/dp/B0DN25LGK8) | direct |

##### MacBook Pro 16 M4 Pro 48GB — Amazon (third-party seller) (refurbished)
Low $2,199.00 · High $2,199.00 · 1 entry

| Date | Price | Basis |
|---|--:|---|
| 2026-11-17 | [$2,199.00](https://www.amazon.com/dp/B0FT4PJ9QP) | direct |

##### MacBook Pro 16 M5 Max 128GB — Amazon (third-party seller) (new)
Low $6,999.00 · High $6,999.00 · 1 entry

| Date | Price | Basis |
|---|--:|---|
| 2026-11-17 | [$6,999.00](https://www.amazon.com/dp/B0GYZYQC19) | direct |

##### MacBook Pro 16 M5 Max 48GB — Amazon (new)
Low $4,499.00 · High $4,499.00 · 1 entry

| Date | Price | Basis |
|---|--:|---|
| 2026-11-17 | [$4,499.00](https://www.amazon.com/dp/B0GR1G6V6H) | direct |

##### MacBook Pro 16 M5 Max 48GB — Apple (Certified Refurbished) (refurbished)
Low $4,249.00 · High $4,249.00 · 1 entry

| Date | Price | Basis |
|---|--:|---|
| 2026-11-17 | [$4,249.00](https://www.apple.com/shop/product/fge94ll/a/Refurbished-16-inch-MacBook-Pro-Apple-M5-Max-chip-with-18%E2%80%91Core-CPU-and-40%E2%80%91Core-GPU-Silver) | direct |

##### MacBook Pro 16 M5 Pro 48GB — Apple (Certified Refurbished) (refurbished)
Low $3,059.00 · High $3,059.00 · 1 entry

| Date | Price | Basis |
|---|--:|---|
| 2026-11-17 | [$3,059.00](https://www.apple.com/shop/product/fgec4ll/a/Refurbished-16-inch-MacBook-Pro-Apple-M5-Pro-chip-with-18%E2%80%91Core-CPU-and-20%E2%80%91Core-GPU-Space-Black) | direct |

##### MacBook Pro 16 M5 Pro 64GB — Amazon (third-party seller) (new)
Low $4,599.00 · High $4,599.00 · 1 entry

| Date | Price | Basis |
|---|--:|---|
| 2026-11-17 | [$4,599.00](https://www.amazon.com/dp/B0H7Z68CLL) | direct |

</details>

🔥 = DEAL: a new 4TB TLC SSD at $450.00 or less (SSDs only); or, in any category, a price at least 10% below the previous logged price for the same item, store and condition, or strictly below every earlier price for that item and condition once prices.csv has at least 7 days of history. Change is against the previous logged price for the same item, store and condition.

<sub>Generated from [`prices.csv`](prices.csv) by [`scripts/build_readme.py`](scripts/build_readme.py). Daily notes are in [`claude.md`](claude.md).</sub>
<!-- PRICES:END -->
