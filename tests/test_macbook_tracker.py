"""Offline tests for scripts/track_macbooks.py."""
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import price_log  # noqa: E402
import track_macbooks as tm  # noqa: E402

RUN_DATE = "2026-11-17"
AMAZON_TITLE = ("MacBook Pro Laptop with M5 Max, 18‑core CPU, 40‑core GPU: Standard "
                "14.2-inch Display, 64GB Unified Memory, 2TB SSD Storage; Silver")


def tile(title, memory, price, model="macbookpro", size="16inch", capacity="2tb"):
    return {
        "title": title, "productDetailsUrl": "/shop/product/abc/refurbished-macbook?fnode=1",
        "price": {"currentPrice": {"raw_amount": price}},
        "filters": {"dimensions": {"refurbClearModel": model, "dimensionScreensize": size,
                                   "tsMemorySize": memory, "dimensionCapacity": capacity}},
    }


def search_result(asin, title, price):
    cost = f'<span class="a-price"><span class="a-offscreen">${price}</span></span>' if price else ""
    return (f'<div role="listitem" data-asin="{asin}" data-component-type="s-search-result">'
            f'<h2 class="a-size-mini"><span>Apple</span></h2>'
            f'<h2 aria-label="{title}" class="a-size-medium"><span>{title}</span></h2>{cost}</div>')


def product_page(title, price="5,099.00", stock="In Stock", seller="Some Seller"):
    return (f'<span id="productTitle"> {title} </span><div id="corePrice_feature_div">'
            f'<span class="a-offscreen">${price}</span></div>'
            f'<div id="availability"><span>{stock}</span></div>'
            f'<a id="sellerProfileTriggerId" href="/x">{seller}</a>')


class MacbookTrackerTests(unittest.TestCase):
    def test_parse_config(self):
        config, reason = tm.parse_config(AMAZON_TITLE)
        self.assertIsNone(reason)
        self.assertEqual(tm.item_name(config), "MacBook Pro 14 M5 Max 64GB")
        self.assertEqual(tm.spec_text(config), "64GB RAM, 2TB SSD, 18C CPU/40C GPU")
        self.assertEqual(config["condition"], "new")
        config, _ = tm.parse_config('Apple MacBook Pro 16" M2 Max 96GB 512GB (Renewed)')
        self.assertEqual((tm.item_name(config), tm.spec_text(config), config["condition"]),
                         ("MacBook Pro 16 M2 Max 96GB", "96GB RAM, 512GB SSD", "refurbished"))

    def test_parse_config_rejects(self):
        cases = {
            "Mac Studio M4 Max 64GB 1TB": "not a MacBook",
            "Hard Case for MacBook Pro 16-inch M4 Max 64GB": "accessory",
            "MacBook Pro M5 Max 64GB 2TB": "no screen size",
            "MacBook Pro 16-inch 64GB 2TB": "no chip",
            "MacBook Pro 16-inch M4 Max / M5 Max 64GB": "more than one chip",
            "MacBook Pro 16-inch M5 Max 2TB": "no memory size",
            "MacBook Pro 16-inch M5 Max 48GB 64GB 2TB": "more than one memory size",
            "MacBook Pro 16-inch M5 Max 64GB 1TB 2TB": "more than one storage size",
        }
        for title, expected in cases.items():
            config, reason = tm.parse_config(title)
            self.assertIsNone(config, title)
            self.assertIn(expected, reason, title)

    def test_refurb_page(self):
        tiles = [
            tile("Refurbished 16-inch MacBook Pro Apple M5 Max chip with 18‑Core CPU and "
                 "40‑Core GPU - Silver", "64gb", "4599.00"),
            tile("Refurbished 16-inch MacBook Pro Apple M5 Max chip with 18‑Core CPU and "
                 "40‑Core GPU - Space Black", "64gb", "4899.00", capacity="4tb"),
            tile("Refurbished 14-inch MacBook Pro Apple M5 chip - Silver", "16gb", "1359.00",
                 size="14inch"),
            tile("Refurbished Mac Studio Apple M3 Ultra chip", "96gb", "4329.00", model="macstudio"),
        ]
        page = f"<script>window.REFURB_GRID_BOOTSTRAP = {json.dumps({'tiles': tiles})};\n</script>"
        parsed = tm.parse_refurb_page(page)
        self.assertEqual(len(parsed), 4)
        rows = [tm.refurb_row(t, RUN_DATE)[0] for t in parsed]
        self.assertEqual([bool(r) for r in rows], [True, True, False, False])
        best = tm.cheapest_rows([r for r in rows if r])
        self.assertEqual(len(best), 1)
        self.assertEqual(
            (best[0]["item"], best[0]["spec"], best[0]["store"], best[0]["condition"],
             best[0]["price_usd"], best[0]["url"]),
            ("MacBook Pro 16 M5 Max 64GB", "64GB RAM, 2TB SSD, 18C CPU/40C GPU",
             "Apple (Certified Refurbished)", "refurbished", "4599.00",
             "https://www.apple.com/shop/product/abc/refurbished-macbook"))
        self.assertEqual(price_log.validate_row(best[0], RUN_DATE), [])
        self.assertIsNone(tm.parse_refurb_page("<html>no data</html>"))

    def test_amazon_search(self):
        page = "<html>" + "".join([
            search_result("B000000001", AMAZON_TITLE, "5,099.00"),
            search_result("B000000002", AMAZON_TITLE.replace("Silver", "Space Black"), "5,049.00"),
            search_result("B000000003", AMAZON_TITLE.replace("64GB", "36GB"), "4,099.00"),
            search_result("B000000004", AMAZON_TITLE.replace("64GB", "128GB"), None),
            search_result("B000000005", "96W Charger for MacBook Pro", "29.99"),
        ]) + "</html>"
        results = tm.parse_search_page(page)
        self.assertEqual([r["asin"][-1] for r in results], list("12345"))
        self.assertEqual(results[0]["price"], 5099.00)
        groups, skipped = tm.amazon_candidates(results)
        self.assertEqual(list(groups), [("MacBook Pro 14 M5 Max 64GB", "new")])
        self.assertEqual([c["asin"][-1] for c in groups[("MacBook Pro 14 M5 Max 64GB", "new")]],
                         ["2", "1"])
        self.assertEqual(sorted(s["reason"] for s in skipped),
                         ["accessory, part or bundle listing", "no price in search results"])
        self.assertEqual(tm.parse_search_page("<html>Robot check</html>"), [])

    def test_amazon_row(self):
        config, _ = tm.parse_config(AMAZON_TITLE)
        candidate = {"asin": "B000000001", "config": config}
        parse = tm.parse_product_page
        row, reason = tm.amazon_row(parse(product_page(AMAZON_TITLE)), candidate, RUN_DATE)
        self.assertIsNone(reason)
        self.assertEqual((row["store"], row["price_usd"], row["url"]),
                         ("Amazon (third-party seller)", "5099.00",
                          "https://www.amazon.com/dp/B000000001"))
        self.assertEqual(price_log.validate_row(row, RUN_DATE), [])
        row, _ = tm.amazon_row(parse(product_page(AMAZON_TITLE, seller="Amazon.com")),
                               candidate, RUN_DATE)
        self.assertEqual(row["store"], "Amazon")
        other = parse(product_page(AMAZON_TITLE.replace("64GB", "128GB")))
        self.assertIn("different configuration", tm.amazon_row(other, candidate, RUN_DATE)[1])
        gone = parse(product_page(AMAZON_TITLE, stock="Currently unavailable."))
        self.assertIn("not in stock", tm.amazon_row(gone, candidate, RUN_DATE)[1])


if __name__ == "__main__":
    unittest.main()
