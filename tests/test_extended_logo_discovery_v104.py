from __future__ import annotations

import unittest
from unittest.mock import patch

from services.logo_discovery_service import _candidate_score, _url_variants


class ExtendedLogoDiscoveryTests(unittest.TestCase):
    @patch("services.logo_discovery_service.validate_remote_url", return_value=True)
    def test_url_variants_include_root_and_www(self, _mock):
        variants = _url_variants("https://example.com/docs/product")
        self.assertIn("https://example.com/", variants)
        self.assertTrue(any("www.example.com" in value for value in variants))

    def test_large_manifest_icon_scores_above_plain_icon(self):
        manifest = _candidate_score(
            "manifest-icon", True, "https://example.com/icon-512.png", declared_sizes="512x512"
        )
        plain = _candidate_score("icon", True, "https://example.com/favicon.ico")
        self.assertGreater(manifest, plain)


if __name__ == "__main__":
    unittest.main()
