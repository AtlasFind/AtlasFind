import unittest
from html import unescape

from app import app


class MediaKitTests(unittest.TestCase):
    def setUp(self):
        app.config.update(TESTING=True)
        self.client = app.test_client()

    def test_turkish_collaboration_page_has_current_media_kit(self):
        response = self.client.get("/tr/collaborate")
        page = unescape(response.get_data(as_text=True))
        self.assertEqual(response.status_code, 200)
        self.assertIn('class="media-kit"', page)
        self.assertIn("1.000'den fazla", page)
        self.assertIn("Profil logosunu indir", page)
        self.assertIn("Sosyal paylaşım görselini indir", page)
        self.assertNotIn("600 aracı", page)

    def test_english_collaboration_page_has_media_kit(self):
        page = self.client.get("/en/collaborate").get_data(as_text=True)
        self.assertIn("Everything you need to introduce AtlasFind", page)
        self.assertIn("more than 1,000 tools", page)
        self.assertIn("Download profile logo", page)


if __name__ == "__main__":
    unittest.main()
