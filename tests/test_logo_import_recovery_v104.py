from __future__ import annotations

import unittest

from services.logo_import_service import _ascii_safe_url, _sniff_content_type


class LogoImportRecoveryTests(unittest.TestCase):
    def test_non_ascii_url_is_encoded(self):
        result = _ascii_safe_url("https://example.com/х-logo.png")
        self.assertIn("%D1%85", result)

    def test_octet_stream_png_can_be_sniffed(self):
        self.assertEqual(_sniff_content_type(b"\x89PNG\r\n\x1a\nrest"), "image/png")

    def test_html_is_not_treated_as_image(self):
        self.assertIsNone(_sniff_content_type(b"<html><body>no</body></html>"))


if __name__ == "__main__":
    unittest.main()
