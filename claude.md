# Nitro V 16S Hardware Price Watch (`claude.md`)

## 1. Purpose & Schedule
A cloud routine runs daily at **9:00 AM Eastern** to track current US street prices across five hardware upgrade categories for an **Acer Nitro V 16S (ANV16S-71)** laptop setup.

**CSV-Only Output Rule:** Each run **must only write to `prices.csv`** (appending rows with their source date). Do **not** modify or append logs to `claude.md`, `README.md` (auto-regenerated from `prices.csv` by GitHub Actions), `scripts/build_readme.py`, `scripts/visualize_prices.py`, or any other file in the repository.

---

## 2. Tracked Categories & Target Specs

### (1) `ssd` — 4 TB M.2 2280 NVMe PCIe 4.0 (No Heatsink)
* **Compatibility:** M.2 2280, NVMe, PCIe 4.0, single- or double-sided **without heatsink** (must fit Acer Nitro V 16S internal slot).
* **Primary Models (4 TB):**
  * Lexar NM790
  * TeamGroup MP44, MP44Q, T-Force G50 / G50 Evo
  * WD Black SN7100 (or SanDisk Optimus GX 7100), SN850X (or SanDisk Optimus GX PRO 850X)
  * WD Blue SN5000, SN5100
  * Samsung 990 EVO Plus, 990 Pro
  * Crucial T500, P310
  * Kingston KC3000
  * Silicon Power UD90
  * Other reputable tier-1 brands meeting the exact spec.
* **Special Target — Micron 2500:** Check for a 4 TB version (`MTFDKBA4T0QGN`). If no 4 TB version exists, check and log the 2 TB version (`MTFDKBA2T0QGN`).
* **Exclusions:** PCIe 5.0 drives (unless priced below the cheapest qualifying Gen 4 drive), drives with pre-installed heatsinks/PS5 editions, and unverified off-brand drives. Always record NAND flash type (`TLC` vs. `QLC`) in `spec`.

### (2) `ram` — Single 64 GB DDR5 SO-DIMM Module
* **Specs:** 1x64 GB (single module only), DDR5 SO-DIMM (262-pin laptop form factor), non-ECC, unbuffered, **5600 MT/s or faster**.
* **Known Part Numbers / Lines:** Crucial `CT64G56C46S5`, G.Skill Ripjaws `F5-5600S4645A64GX1-RS`, Kingston FURY Impact, Corsair Vengeance, TeamGroup Elite, Samsung/SK Hynix/Micron OEM 64 GB modules.
* **Exclusions:** 2x32 GB kits, desktop UDIMMs/CUDIMMs, ECC/registered modules, or speeds below DDR5-5600 (do not log to `prices.csv`).

### (3) `nvidia_gpu` — High-VRAM Desktop NVIDIA GPUs
* **Models:** GeForce RTX 5090 (32 GB), RTX 4090 (24 GB), RTX 3090 Ti (24 GB), RTX 3090 (24 GB).
* **Tracking Target:** Log the **cheapest New** listing and the **cheapest Used/Refurbished** listing for each model.

### (4) `amd_gpu` — High-End Desktop AMD Radeon GPUs
* **Models:** Radeon RX 9070 XT, RX 9070, RX 7900 XTX, RX 7900 XT, plus **any newer Radeon model positioned above the RX 9070 XT**.
* **Tracking Target:** Log the **cheapest New** listing and the **cheapest Used/Refurbished** listing for each model.

### (5) `egpu` — Thunderbolt / USB4 External GPU Solutions
* **Specs:** Thunderbolt 3/4/5 or USB4 enclosures and complete all-in-one external GPUs (e.g., Razer Core X V2, Sonnet Breakaway Box 850 T5 / 750ex, AOOSTAR AG02, GPD G1, ONEXGPU).
* **Details to Record (in `spec`):** Type (`Enclosure` vs. `Complete eGPU`), Connection (`TB3`, `TB4`, `TB5`, `USB4`), and PSU (`Built-in XW`, `Included`, or `No PSU / ATX required`).
* **Exclusions:** OCuLink-only docks or proprietary-connector-only docks without Thunderbolt/USB4 support.

---

## 3. Qualifying Stores & Verification Rules

* **Approved Stores (US, USD):** Amazon, eBay, Newegg, Best Buy, Walmart, B&H Photo, Micro Center.
* **No Date Window:** Log every price found by a direct live store check or a price tracker/deal report (`cheapestssd.com`, `PC Gamer`, `9to5Toys`, `videocardprices.com`, `camelcamelcamel`, `Keepa`, etc.), **whatever its age**. Record the date the source gives in `source_date`; if the source gives no date, use the run date (the day the price was seen).
* **Still Excluded:** Out-of-stock prices and multi-listing tracker averages (such as eBay lowest-three averages or median asks).
* **eBay Used/Refurbished:** eBay used and refurbished listings are allowed, including ones reported by a tracker. Seller feedback and return policy do not have to be verified.
* **Three-Strike Fetch Fallback:** If direct page fetches fail on **3 consecutive attempts** (e.g., HTTP 403/503, truncated output, or captcha on PCPartPicker, Newegg, Best Buy, Micro Center, Walmart), immediately switch to web search and aggregator snapshots for the remainder of the run. Mention blocked sites only in the run's final response/commit message, never in `claude.md`.

---

## 4. DEAL Flag Criteria

`scripts/build_readme.py` and `scripts/visualize_prices.py` automatically flag **`DEAL`** items from `prices.csv` when any of the following hold (mention triggered deals in the run response/commit summary if applicable):
1. **SSD Threshold:** A **new 4 TB TLC SSD** from a reputable brand priced at **$450.00 or less**.
2. **10% Price Drop:** Any tracked item (in any of the 5 categories) priced **at least 10% below** its most recent earlier price in `prices.csv` (matching `category`, `item`, `store`, and `condition`).
3. **All-Time Low (7+ Days History):** Once `prices.csv` contains at least 7 distinct dates of history, any tracked item priced **strictly below every earlier logged price** for that `category`, `item`, and `condition` (across any store).

---

## 5. `prices.csv` Schema & Write Rules

Maintain `prices.csv` using the unified 10-column header:

```csv
date,category,item,spec,store,condition,price_usd,basis,source_date,url
```

* `date`: Run date (`YYYY-MM-DD`).
* `category`: One of `ssd`, `ram`, `nvidia_gpu`, `amd_gpu`, `egpu`.
* `item`: Normalized model name, kept consistent with existing `prices.csv` entries for series continuity (e.g., `Silicon Power UD90`, `Crucial CT64G56C46S5`, `RTX 5090 (ASUS TUF Gaming OC)`).
* `spec`: Capacity and flash type for SSDs (`4TB TLC`, `4TB QLC`, `2TB TLC` — capacity must appear in `spec` for `scripts/build_readme.py`), module size/speed/CL for RAM (`1x64GB DDR5-5600 CL46`), VRAM/memory type for GPUs (`32GB GDDR7`, `24GB GDDR6X`), or type/connection/PSU for eGPUs (`Enclosure, TB5, No PSU`).
* `store`: Store name (note third-party seller if applicable, e.g., `Amazon (third-party seller)`).
* `condition`: Lowercase `new`, `used`, or `refurbished` (lowercase required by `scripts/build_readme.py`).
* `price_usd`: Numeric price without `$` or commas (e.g., `475.00`).
* `basis`: `direct` or `reported (<Source Name>)`.
* `source_date`: Date the price was observed or reported (`YYYY-MM-DD`); the run date when the source is undated.
* `url`: Direct listing URL or reporting article URL.

### Write Constraints
* **Allowed File:** Append new rows to `prices.csv` **only**.
* **No Other File Edits:** Never edit `claude.md`, `README.md`, or scripts during a scheduled price-check run.
* **No Placeholder Rows:** If no qualifying price is found for an item or category, omit it from `prices.csv` rather than writing `None found` or empty rows.
* **Run Reporting:** Put any brief summary, blocked-site notes, or notable deals in the run response / commit message rather than modifying repository markdown files.
