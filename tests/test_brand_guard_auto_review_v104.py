from __future__ import annotations

import unittest

from scripts.auto_review_logo_candidates_v104 import _product_relevance


class BrandGuardTests(unittest.TestCase):
    def test_rejects_generic_apple_icon_for_logic_pro(self):
        item = {
            "slug": "logic-pro",
            "name": "Logic Pro",
            "official_url": "https://www.apple.com/logic-pro/",
        }
        candidate = {
            "url": "https://www.apple.com/apple-touch-icon.png",
            "source_page": "https://www.apple.com/logic-pro/",
        }
        self.assertEqual(_product_relevance(item, candidate), (False, "generic_corporate_asset"))

    def test_accepts_product_specific_firefox_icon(self):
        item = {
            "slug": "mozilla-firefox",
            "name": "Mozilla Firefox",
            "official_url": "https://www.firefox.com/",
        }
        candidate = {
            "url": "https://www.firefox.com/media/firefox/apple-touch-icon.png",
            "source_page": "https://www.firefox.com/",
        }
        self.assertTrue(_product_relevance(item, candidate)[0])

    def test_rejects_generic_aws_asset_for_s3(self):
        item = {
            "slug": "amazon-s3",
            "name": "Amazon S3",
            "official_url": "https://aws.amazon.com/s3/",
        }
        candidate = {
            "url": "https://a0.awsstatic.com/site/touch-icon-ipad-144-smile.png",
            "source_page": "https://aws.amazon.com/s3/",
        }
        self.assertFalse(_product_relevance(item, candidate)[0])

    def test_rejects_generic_microsoft_icon_for_onedrive(self):
        item = {
            "slug": "microsoft-onedrive",
            "name": "Microsoft OneDrive",
            "official_url": "https://www.microsoft.com/microsoft-365/onedrive/online-cloud-storage",
        }
        candidate = {
            "url": "https://www.microsoft.com/favicon.ico",
            "source_page": item["official_url"],
        }
        self.assertEqual(
            _product_relevance(item, candidate),
            (False, "generic_corporate_asset"),
        )

    def test_accepts_product_specific_onedrive_asset(self):
        item = {
            "slug": "microsoft-onedrive",
            "name": "Microsoft OneDrive",
            "official_url": "https://www.microsoft.com/microsoft-365/onedrive/online-cloud-storage",
        }
        candidate = {
            "url": "https://cdn.example.com/microsoft/onedrive/icon-192.png",
            "source_page": item["official_url"],
        }
        self.assertEqual(_product_relevance(item, candidate), (True, "product_match"))


if __name__ == "__main__":
    unittest.main()
