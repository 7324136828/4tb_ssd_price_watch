"""Offline tests for scripts/track_ram.py."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import price_log  # noqa: E402
import track_ram  # noqa: E402

PAGE = """
<span id="productTitle" class="a-size-large">  Crucial 64GB DDR5 RAM 5600MHz Laptop Memory,
 SODIMM 262-Pin &ndash; CT64G56C46S5 </span>
<div id="corePrice_feature_div"><span class="a-price"><span class="a-offscreen">$1,199.89</span></span></div>
<div id="availability" class="a-section"><span class="a-color-success"> Only 17 left in stock - order soon. </span></div>
<a id="sellerProfileTriggerId" href="/x">PChome-1</a>
"""
ARGS = ("B0DSQWZ5G2", "Crucial CT64G56C46S5", "CT64G56C46S5", "1x64GB DDR5-5600 CL46", "2026-11-15")


class RamTrackerTests(unittest.TestCase):
    def test_parse(self):
        page = track_ram.parse_product_page(PAGE)
        self.assertTrue(page["title"].endswith("CT64G56C46S5"))
        self.assertEqual(page["price"], 1199.89)
        self.assertEqual(page["availability"], "Only 17 left in stock - order soon.")
        self.assertEqual(page["seller"], "PChome-1")

    def test_row(self):
        row, reason = track_ram.evaluate(track_ram.parse_product_page(PAGE), *ARGS)
        self.assertIsNone(reason)
        self.assertEqual((row["item"], row["store"], row["condition"], row["price_usd"]),
                         ("Crucial CT64G56C46S5", "Amazon (third-party seller)", "new", "1199.89"))
        self.assertEqual(row["url"], "https://www.amazon.com/dp/B0DSQWZ5G2")
        self.assertEqual(price_log.validate_row(row, "2026-11-15"), [])

    def test_sold_by_amazon(self):
        page = dict(track_ram.parse_product_page(PAGE), seller="Amazon.com")
        self.assertEqual(track_ram.evaluate(page, *ARGS)[0]["store"], "Amazon")

    def test_skips(self):
        page = track_ram.parse_product_page(PAGE)
        self.assertIn("not in stock", track_ram.evaluate(
            dict(page, availability="Currently unavailable."), *ARGS)[1])
        self.assertEqual(track_ram.evaluate(dict(page, price=None), *ARGS)[1], "no price")
        self.assertIn("does not mention", track_ram.evaluate(
            dict(page, title="Some 2x32GB kit"), *ARGS)[1])

    def test_blocked_page(self):
        page = track_ram.parse_product_page("<html>Robot check</html>")
        self.assertEqual((page["title"], page["price"]), ("", None))


if __name__ == "__main__":
    unittest.main()
