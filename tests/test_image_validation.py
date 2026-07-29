import tempfile
import unittest
from pathlib import Path
from validators.image_validator import safe_local_path, validate_source_url, validate_svg
from services.image_service import normalize_branding, resolve_tool_image

class ImageValidationTests(unittest.TestCase):
    def test_path_traversal_is_rejected(self):
        self.assertIsNone(safe_local_path("../../app.py"))
    def test_only_https_sources_are_allowed(self):
        self.assertTrue(validate_source_url("https://example.com/brand"))
        self.assertFalse(validate_source_url("http://example.com/logo.png"))
        self.assertFalse(validate_source_url("file:///tmp/logo.png"))
        self.assertFalse(validate_source_url("https://127.0.0.1/logo.png"))
    def test_dangerous_svg_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bad.svg"
            path.write_text('<svg xmlns="http://www.w3.org/2000/svg"><script>alert(1)</script></svg>', encoding="utf-8")
            self.assertTrue(validate_svg(path))
    def test_missing_logo_uses_local_fallback(self):
        tool = {"name": "Example Tool", "slug": "example-tool"}
        self.assertEqual(normalize_branding(tool)["logo"]["status"], "missing")
        resolved = resolve_tool_image(tool)
        self.assertTrue(resolved["is_fallback"])
        self.assertTrue(resolved["url"].startswith("/static/icons/generated/"))

if __name__ == "__main__":
    unittest.main()
