import unittest

from app import app


class HomepageUpgradeTests(unittest.TestCase):
    def setUp(self):
        app.config.update(TESTING=True)
        self.client = app.test_client()

    def test_homepage_has_discovery_and_trust_sections_in_both_languages(self):
        for locale, heading in (("tr", "Doğru araca daha kısa yoldan ulaş"), ("en", "Reach the right tool faster")):
            response = self.client.get(f"/{locale}/")
            self.assertEqual(response.status_code, 200)
            page = response.get_data(as_text=True)
            self.assertIn('class="hero-proof"', page)
            self.assertIn('class="home-showcase-grid"', page)
            self.assertIn(heading, page)

    def test_category_cards_use_canonical_localized_links(self):
        page = self.client.get("/tr/").get_data(as_text=True)
        self.assertIn('href="/tr/categories/design-and-graphics"', page)
        self.assertIn('href="/tr/categories/video-and-animation"', page)
        self.assertNotIn('href="/categories/design"', page)
        self.assertNotIn('href="/categories/video"', page)

    def test_filtered_home_hides_showcase_and_localizes_results(self):
        page = self.client.get("/tr/?pricing=free").get_data(as_text=True)
        self.assertNotIn('class="home-showcase-grid"', page)
        self.assertIn("araçtan", page)
        self.assertNotIn(" of 1000 tools", page)
        self.assertIn("Ücretsiz", page)
        self.assertIn("Hafif", page)


if __name__ == "__main__":
    unittest.main()
