"""Offline tests for scripts/track_gpus.py, scripts/price_log.py and scripts/add_price.py."""
import csv
import html
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import add_price  # noqa: E402
import price_log  # noqa: E402
import track_gpus  # noqa: E402


def astro(value):
    """Encode a value the way Astro serialises island props."""
    if isinstance(value, list):
        return [1, [astro(v) for v in value]]
    if isinstance(value, dict):
        return [0, {k: astro(v) for k, v in value.items()}]
    return [0, value]


def card_page(card):
    props = {k: astro(v) for k, v in {"card": card}.items()}
    attr = html.escape(json.dumps(props), quote=True)
    return f'<html><body><astro-island uid="x" props="{attr}"></astro-island></body></html>'


CARD = {
    "id": "amd-rx-9070-xt",
    "name": "GIGABYTE Radeon RX 9070 XT Gaming OC 16G Graphics Card, PCIe 5.0, 16GB GDDR6",
    "model": "Radeon RX 9070 XT",
    "price": 1034.99,
    "specs": {"memory": "16 GB", "memoryType": "GDDR6"},
    "inStock": True,
    "amazonUrl": "https://www.amazon.com/dp/B0TEST",
    "lastUpdated": "2026-11-14T14:38:23.021616+00:00",
    "productBrand": "GIGABYTE",
    "prices": [
        {"source": "ebay", "condition": "used", "price": 899,
         "url": "https://www.ebay.com/itm/1", "inStock": True,
         "listingTitle": "PowerColor Radeon RX 9070 XT OC 16GB", "fetchedAt": "2026-11-14T14:39:54Z"},
        {"source": "newegg", "condition": "new", "price": 949.99,
         "url": "https://www.newegg.com/p/N82E1", "inStock": True,
         "listingTitle": "ASRock Challenger Radeon RX 9070 XT Graphics Card RX9070XT CL 16G",
         "fetchedAt": "2026-11-14T14:39:39.448Z"},
        {"source": "newegg", "condition": "new", "price": 500,
         "url": "https://www.newegg.com/p/wrong", "inStock": True,
         "listingTitle": "Sapphire Pulse Radeon RX 9070 16GB", "fetchedAt": "2026-11-14T10:00:00Z"},
    ],
}


class ParsingTests(unittest.TestCase):
    def test_parse_card_page_decodes_props(self):
        card = track_gpus.parse_card_page(card_page(CARD))
        self.assertEqual(card["price"], 1034.99)
        self.assertEqual(card["prices"][1]["source"], "newegg")
        self.assertEqual(card["specs"]["memory"], "16 GB")

    def test_parse_card_page_without_card(self):
        self.assertIsNone(track_gpus.parse_card_page("<html></html>"))

    def test_normalize_model(self):
        n = track_gpus.normalize_model
        self.assertEqual(n("GeForce RTX 3090 Ti 24GB"), "RTX 3090 Ti")
        self.assertEqual(n("ASRock RX9070XT CL 16G"), "RX 9070 XT")
        self.assertEqual(n("Radeon RX 7900 XTX"), "RX 7900 XTX")
        self.assertEqual(n("Radeon RX 9070 Graphics"), "RX 9070")
        self.assertIsNone(n("Arc B580"))

    def test_variant_names_match_existing_csv_style(self):
        v = track_gpus.variant_name
        self.assertEqual(v("ASUS TUF Gaming GeForce RTX 5090 32GB GDDR7 OC Edition Gaming "
                           "Graphics Card", "ASUS"), "ASUS TUF Gaming OC")
        self.assertEqual(v(CARD["name"], "GIGABYTE"), "GIGABYTE Gaming OC")
        self.assertEqual(v("ASRock Challenger Radeon RX 9070 XT Graphics Card RX9070XT CL 16G"),
                         "ASRock Challenger")
        self.assertEqual(v("ASUS RTX 5090 32GB ROG Astral OC Edition GPU In Warranty"),
                         "ASUS ROG Astral OC")

    def test_discover_newer_radeons(self):
        home = ('<a href="/card/amd-rx-9070-xt/"></a><a href="/card/amd-rx-9080-xt/"></a>'
                '<a href="/card/nvidia-rtx-5090/"></a><a href="/card/amd-rx-7600/"></a>')
        self.assertEqual(track_gpus.discover_newer_radeons(home), {"RX 9080 XT": "amd-rx-9080-xt"})

    def test_iso_date(self):
        self.assertEqual(track_gpus.iso_date("2026-11-14T23:30:00-05:00"), "2026-11-15")
        self.assertEqual(track_gpus.iso_date("2026-11-14T14:39:39.448Z"), "2026-11-14")
        self.assertIsNone(track_gpus.iso_date(None))


FALLBACK_PAGE = """
<div class="buy-now-buttons"><a href="https://www.amazon.com/dp/B0TEST?tag=x&amp;th=1" class="buy-now-btn amazon" target="_blank">
 <span class="retailer-name">Amazon</span> <span class="price">$5,500</span> </a><a href="https://www.ebay.com/itm/123?mkcid=1&amp;campid=2" class="buy-now-btn ebay" target="_blank">
 <span class="retailer-name">Ebay</span> <span class="price">$1,300</span> </a></div>
<a href="https://www.amazon.com/dp/OTHER" class="header-price-button amazon"><span class="price">$7,499</span></a>
<p class="date-generated">Date Generated: Sun Nov 15 2026 03:10:36 GMT+0000 (Coordinated Universal Time)</p>
"""


class FallbackTests(unittest.TestCase):
    def test_slug(self):
        self.assertEqual(track_gpus.fallback_slug("RTX 3090 Ti"), "rtx-3090-ti")
        self.assertEqual(track_gpus.fallback_slug("RX 7900 XT"), "rx-7900-xt")

    def test_parse_and_evaluate(self):
        listings, page_date = track_gpus.parse_fallback_page(FALLBACK_PAGE)
        self.assertEqual(page_date, "2026-11-15")
        self.assertEqual(listings, [
            {"source": "amazon", "url": "https://www.amazon.com/dp/B0TEST", "price": 5500.0},
            {"source": "ebay", "url": "https://www.ebay.com/itm/123", "price": 1300.0},
        ])
        rows, skipped = track_gpus.evaluate_fallback(
            listings, page_date, "RTX 4090", "nvidia_gpu", "24GB GDDR6X", "2026-11-15")
        self.assertEqual(skipped, [])
        self.assertEqual([(r["item"], r["store"], r["condition"], r["price_usd"]) for r in rows], [
            ("RTX 4090", "Amazon", "new", "5500.00"),
            ("RTX 4090", "eBay", "used", "1300.00"),
        ])
        for r in rows:
            self.assertEqual(r["basis"], "reported (gpudeals.net)")
            self.assertEqual(price_log.validate_row(r, "2026-11-15"), [])

    def test_empty_page(self):
        self.assertEqual(track_gpus.parse_fallback_page("<html></html>"), ([], None))


class EvaluateTests(unittest.TestCase):
    def evaluate(self, run_date="2026-11-15", card=CARD):
        return track_gpus.evaluate(card, "RX 9070 XT", "amd_gpu", "16GB GDDR6", run_date,
                                   "https://videocardprices.com/card/amd-rx-9070-xt/")

    def test_rows_and_skips(self):
        rows, skipped = self.evaluate()
        self.assertEqual([(r["item"], r["store"], r["price_usd"]) for r in rows], [
            ("RX 9070 XT (GIGABYTE Gaming OC)", "Amazon", "1034.99"),
            ("RX 9070 XT (PowerColor OC)", "eBay", "899.00"),  # used eBay is logged
            ("RX 9070 XT (ASRock Challenger)", "Newegg", "949.99"),
        ])
        for r in rows:
            self.assertEqual(r["spec"], "16GB GDDR6")
            self.assertEqual(r["source_date"], "2026-11-14")
            self.assertEqual(r["basis"], "reported (videocardprices.com)")
            self.assertEqual(price_log.validate_row(r, "2026-11-15"), [])
        reasons = " | ".join(s["reason"] for s in skipped)
        self.assertIn("RX 9070, not RX 9070 XT", reasons)  # wrong model on the page

    def test_old_prices_are_logged(self):
        rows, _ = self.evaluate(run_date="2027-03-01")
        self.assertEqual(len(rows), 3)
        self.assertEqual({r["source_date"] for r in rows}, {"2026-11-14"})

    def test_future_prices_are_skipped(self):
        rows, skipped = self.evaluate(run_date="2026-11-10")
        self.assertEqual(rows, [])
        self.assertTrue(any("after the run date" in s["reason"] for s in skipped))

    def test_undated_listing_uses_run_date(self):
        card = dict(CARD, lastUpdated=None, prices=[])
        rows, _ = self.evaluate(card=card)
        self.assertEqual(rows[0]["source_date"], "2026-11-15")

    def test_out_of_stock_is_skipped(self):
        card = dict(CARD, inStock=False, prices=[])
        rows, skipped = self.evaluate(card=card)
        self.assertEqual(rows, [])
        self.assertEqual(skipped[0]["reason"], "out of stock")


class PriceLogTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.csv = Path(self.tmp.name) / "prices.csv"
        self.csv.write_text(",".join(price_log.FIELDS) + "\n", encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def read(self):
        with self.csv.open(newline="", encoding="utf-8") as f:
            return list(csv.DictReader(f))

    def row(self, **kw):
        base = {"date": "2026-11-15", "category": "nvidia_gpu", "item": "RTX 4090 (MSI)",
                "spec": "24GB GDDR6X", "store": "eBay", "condition": "used",
                "price_usd": "1899", "basis": "direct", "source_date": "2026-11-15",
                "url": "https://www.ebay.com/itm/1"}
        base.update(kw)
        return base

    def test_any_age_but_not_future(self):
        self.assertTrue(price_log.not_in_future("2026-11-15", "2026-11-15"))
        self.assertTrue(price_log.not_in_future("2025-01-01", "2026-11-15"))
        self.assertFalse(price_log.not_in_future("2026-11-16", "2026-11-15"))

    def test_validate_row_catches_problems(self):
        self.assertEqual(price_log.validate_row(self.row()), [])
        bad = price_log.validate_row(self.row(condition="New", store="Etsy",
                                              price_usd="$1,899", basis="PC Gamer"))
        self.assertEqual(len(bad), 4)
        self.assertTrue(price_log.validate_row(self.row(category="ssd", spec="TLC")))

    def test_append_dedupes_and_formats(self):
        added, dupes = price_log.append_rows([self.row(), self.row(price_usd="1850")], self.csv)
        self.assertEqual((len(added), len(dupes)), (1, 1))
        added, dupes = price_log.append_rows([self.row()], self.csv)
        self.assertEqual((len(added), len(dupes)), (0, 1))
        rows = self.read()
        self.assertEqual(rows[0]["price_usd"], "1899.00")

    def test_append_handles_missing_trailing_newline(self):
        self.csv.write_text(",".join(price_log.FIELDS), encoding="utf-8")
        price_log.append_rows([self.row()], self.csv)
        rows = self.read()
        self.assertEqual(len(rows), 1)

    def test_add_price_cli(self):
        args = ["nvidia_gpu", "RTX 4090 (MSI)", "24GB GDDR6X", "eBay", "used", "$1,899.00",
                "https://www.ebay.com/itm/1", "--date", "2026-11-15", "--csv", str(self.csv)]
        self.assertEqual(add_price.main(args), 0)
        self.assertEqual(add_price.main(args[:5] + ["abc"] + args[6:]), 2)
        rows = self.read()
        self.assertEqual([r["price_usd"] for r in rows], ["1899.00"])


if __name__ == "__main__":
    unittest.main()
