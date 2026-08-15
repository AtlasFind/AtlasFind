import json
import unittest
from io import BytesIO

from PIL import Image

from app import app


class FaviconSetupTests(unittest.TestCase):
    def setUp(self):
        app.config.update(TESTING=True)
        self.client = app.test_client()

    def test_google_compatible_48_pixel_icon_is_primary(self):
        page = self.client.get("/tr/").get_data(as_text=True)
        primary = '<link rel="icon" type="image/png" sizes="48x48" href="/static/images/favicon-48.png">'
        self.assertIn(primary, page)
        self.assertLess(page.index(primary), page.index('rel="shortcut icon"'))

        response = self.client.get("/static/images/favicon-48.png")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "image/png")
        self.assertEqual(Image.open(BytesIO(response.data)).size, (48, 48))
        response.close()

    def test_manifest_uses_standard_icon_sizes(self):
        response = self.client.get("/static/site.webmanifest")
        manifest = json.loads(response.get_data(as_text=True))
        response.close()
        sizes = {item["sizes"] for item in manifest["icons"]}
        self.assertTrue({"48x48", "192x192", "512x512"}.issubset(sizes))


if __name__ == "__main__":
    unittest.main()
