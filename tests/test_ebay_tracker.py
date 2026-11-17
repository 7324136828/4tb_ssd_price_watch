"""Offline tests for scripts/track_ebay.py."""
import sys
import unittest
import urllib.parse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import price_log  # noqa: E402
import track_ebay  # noqa: E402

RUN_DATE = "2026-11-16"
TARGETS = {t["item"]: t for t in track_ebay.targets()}
SSD = TARGETS["Samsung 990 Pro"]
RAM = TARGETS["Crucial CT64G56C46S5"]


def listing(title, price, condition_id="1000", item_id="123456789012", **extra):
    base = {
        "itemId": f"v1|{item_id}|0", "legacyItemId": item_id, "title": title,
        "price": {"value": f"{price:.2f}", "currency": "USD"},
        "conditionId": condition_id, "condition": "x",
        "buyingOptions": ["FIXED_PRICE"], "itemLocation": {"country": "US"},
    }
    base.update(extra)
    return base


class EbayTrackerTests(unittest.TestCase):
    def reason(self, target, *args, **kwargs):
        return track_ebay.reject_reason(target, listing(*args, **kwargs))

    def test_good_listings(self):
        self.assertIsNone(self.reason(SSD, "Samsung 990 PRO 4TB NVMe M.2 2280 SSD MZ-V9P4T0B", 700))
        self.assertIsNone(self.reason(SSD, "Samsung 990 Pro 4 TB PCIe 4.0 SSD", 500, "3000"))
        self.assertIsNone(self.reason(RAM, "Crucial 64GB DDR5 5600 SODIMM CT64G56C46S5 x1", 900))

    def test_ssd_rejects(self):
        cases = {
            "Samsung 990 PRO 1TB 2TB 4TB NVMe SSD": "more than one capacity",
            "Samsung 990 PRO 2TB NVMe SSD": "does not say 4TB",
            "Samsung 990 PRO with Heatsink 4TB SSD": "heatsink",
            "Samsung 990 PRO 4TB for PS5": "heatsink",
            "Samsung 990 EVO Plus 4TB NVMe SSD": "does not name the product",
            "Samsung 990 PRO 4TB EMPTY BOX only": "empty box",
            "Samsung 990 PRO 4TB SSD for parts not working": "parts",
        }
        for title, expected in cases.items():
            self.assertIn(expected, self.reason(SSD, title, 600), title)

    def test_model_patterns_do_not_cross_match(self):
        self.assertIsNotNone(self.reason(TARGETS["TeamGroup MP44"], "TeamGroup MP44Q 4TB SSD", 480))
        self.assertIsNone(self.reason(TARGETS["TeamGroup MP44Q"], "TeamGroup MP44Q 4TB SSD", 480))
        self.assertIsNotNone(self.reason(TARGETS["TeamGroup T-Force G50"],
                                         "T-Force G50 EVO 4TB SSD", 480))
        self.assertIsNone(self.reason(TARGETS["WD Blue SN5100"],
                                      "SanDisk Optimus 5100 4TB NVMe SSD", 480))

    def test_ram_rejects(self):
        for title in ("Crucial 128GB Kit (2x64GB) DDR5 CT64G56C46S5",
                      "CT64G56C46S5 64GB x2 DDR5 SODIMM",
                      "Lot of 4 CT64G56C46S5 64GB DDR5"):
            self.assertIsNotNone(self.reason(RAM, title, 1500), title)
        self.assertIn("does not name", self.reason(RAM, "Crucial 64GB DDR5 5600 SODIMM", 900))

    def test_listing_rules(self):
        title = "Samsung 990 PRO 4TB SSD"
        self.assertIn("floor", self.reason(SSD, title, 49.99))
        self.assertIn("condition", self.reason(SSD, title, 600, "7000"))
        self.assertEqual(self.reason(SSD, title, 600, buyingOptions=["AUCTION"]), "auction only")
        self.assertEqual(self.reason(SSD, title, 600, itemLocation={"country": "CN"}),
                         "not a US listing")
        foreign = dict(listing(title, 600), price={"value": "600", "currency": "GBP"})
        self.assertEqual(track_ebay.reject_reason(SSD, foreign), "not priced in USD")

    def test_cheapest_and_row(self):
        row, skipped = track_ebay.cheapest(SSD, [
            listing("Samsung 990 PRO 1TB 2TB 4TB SSD", 99, "3000", "1"),
            listing("Samsung 990 PRO 4TB SSD", 560, "2500", "2"),
            listing("Samsung 990 PRO 4TB SSD open box", 540, "1500", "3"),
        ], RUN_DATE)
        self.assertEqual(len(skipped), 1)
        self.assertEqual((row["store"], row["condition"], row["price_usd"], row["url"]),
                         ("eBay", "used", "540.00", "https://www.ebay.com/itm/3"))
        self.assertEqual(price_log.validate_row(row, RUN_DATE), [])
        self.assertEqual(track_ebay.cheapest(SSD, [], RUN_DATE), (None, []))

    def test_track_with_fake_api(self):
        calls = []

        def fake(url, headers, data=None):
            if url == track_ebay.TOKEN_URL:
                self.assertTrue(headers["Authorization"].startswith("Basic "))
                return {"access_token": "tok"}
            query = urllib.parse.parse_qs(urllib.parse.urlsplit(url).query)
            calls.append(query)
            self.assertEqual(headers["Authorization"], "Bearer tok")
            if "conditionIds:{1000}" in query["filter"][0]:
                return {"itemSummaries": [listing("Crucial CT64G56C46S5 64GB DDR5", 1100)]}
            return {}

        token = track_ebay.get_token("id", "secret", fake)
        report = track_ebay.track(RUN_DATE, token, "ram", fake, pause=0)
        self.assertEqual(len(calls), 2 * len(track_ebay.RAM_MODULES))
        self.assertEqual(calls[0]["sort"], ["price"])
        self.assertEqual([(r["item"], r["condition"]) for r in report["rows"]],
                         [("Crucial CT64G56C46S5", "new")])
        self.assertEqual(len(report["skipped"]), 1)  # the Crucial listing under the G.Skill search

    def test_macbook_listings(self):
        mac = TARGETS["MacBook Pro 16 M4 Max 64GB"]
        good = 'Apple MacBook Pro 16" M4 Max 16-Core CPU 40-Core GPU 64GB RAM 2TB SSD Space Black'
        self.assertIsNone(self.reason(mac, good, 3200, "3000"))
        row, _ = track_ebay.cheapest(mac, [listing(good, 3200, "3000", "7")], RUN_DATE)
        self.assertEqual((row["category"], row["item"], row["spec"], row["condition"]),
                         ("macbook", "MacBook Pro 16 M4 Max 64GB",
                          "64GB RAM, 2TB SSD, 16C CPU/40C GPU", "used"))
        self.assertEqual(price_log.validate_row(row, RUN_DATE), [])
        cases = {
            'MacBook Pro 14" M4 Max 64GB 1TB': "different configuration",
            'MacBook Pro 16" M4 Max 128GB 2TB': "different configuration",
            'MacBook Pro 16" M4 Max 36GB 48GB 64GB 1TB': "more than one memory",
            'MacBook Pro 16" M4 Max 64GB 1TB iCloud locked': "locked or damaged",
            'MacBook Pro 16" M4 Max 64GB 1TB for parts': "parts",
            'MacBook Pro 16" M4 Max 64GB logic board': "accessory",
        }
        for title, expected in cases.items():
            self.assertIn(expected, self.reason(mac, title, 3200, "3000"), title)
        self.assertIn("floor", self.reason(mac, good, 499))

    def test_missing_keys(self):
        import os
        saved = {k: os.environ.pop(k, None) for k in ("EBAY_CLIENT_ID", "EBAY_CLIENT_SECRET")}
        try:
            self.assertEqual(track_ebay.main([]), 2)
        finally:
            os.environ.update({k: v for k, v in saved.items() if v})


if __name__ == "__main__":
    unittest.main()
