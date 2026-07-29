import unittest
from unittest.mock import patch

from services.logo_discovery_service import discover_logo_candidates
from services.logo_import_service import import_approved_logo

HTML = b'''<html><head><link rel="icon" href="/icon.png"><link rel="manifest" href="/manifest.json"><meta property="og:image" content="/social.png"></head></html>'''
MANIFEST = b'{"icons":[{"src":"/app-512.png","sizes":"512x512","type":"image/png"}]}'


class LogoPipelineTests(unittest.TestCase):
    @patch("services.logo_discovery_service.validate_remote_url", return_value=True)
    @patch("services.logo_discovery_service._read_url")
    def test_discovers_official_candidates(self, read, _validate):
        def fake_read(url, **_kwargs):
            if "manifest" in url:
                return MANIFEST, "application/json", "https://example.com/manifest.json"
            return HTML, "text/html", "https://example.com/"

        read.side_effect = fake_read
        candidates, attempts = discover_logo_candidates("https://example.com/")
        urls = {item["url"] for item in candidates}
        self.assertIn("https://example.com/icon.png", urls)
        self.assertIn("https://example.com/app-512.png", urls)
        self.assertTrue(all(item["requires_review"] for item in candidates))
        self.assertTrue(attempts)

    def test_unapproved_candidate_is_rejected(self):
        with self.assertRaises(ValueError):
            import_approved_logo(
                {"slug": "demo", "name": "Demo"},
                {"url": "https://example.com/logo.png", "review_status": "pending"},
                verified_by="admin",
            )


if __name__ == "__main__":
    unittest.main()
