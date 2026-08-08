import unittest

from app import app


class HomepageUpgradeTests(unittest.TestCase):
    def setUp(self):
        app.config.update(TESTING=True)
        self.client = app.test_client()

    def test_homepage_has_trust_and_ad_inventory_in_both_languages(self):
        for locale, ad_label in (("tr", "Reklam · Sponsorlu alan"), ("en", "Advertisement · Sponsored space")):
            response = self.client.get(f"/{locale}/")
            self.assertEqual(response.status_code, 200)
            page = response.get_data(as_text=True)
            self.assertIn('class="hero-proof"', page)
            self.assertNotIn('class="home-showcase-grid"', page)
            self.assertIn('data-ad-placement="home-leaderboard"', page)
            self.assertIn('data-ad-placement="home-catalog-inline"', page)
            self.assertIn(ad_label, page)

    def test_category_cards_use_canonical_localized_links(self):
        page = self.client.get("/tr/").get_data(as_text=True)
        self.assertIn('href="/tr/categories/design-and-graphics"', page)
        self.assertIn('href="/tr/categories/video-and-animation"', page)
        self.assertNotIn('href="/categories/design"', page)
        self.assertNotIn('href="/categories/video"', page)

    def test_filtered_home_localizes_results(self):
        page = self.client.get("/tr/?pricing=free").get_data(as_text=True)
        self.assertIn("araçtan", page)
        self.assertNotIn(" of 1000 tools", page)
        self.assertIn("Ücretsiz", page)
        self.assertIn("Hafif", page)

    def test_tool_detail_has_disclosed_ad_inventory(self):
        page = self.client.get("/tr/tools/chatgpt").get_data(as_text=True)
        self.assertIn('data-ad-placement="tool-detail-footer"', page)
        self.assertIn("Reklam · Sponsorlu alan", page)
        self.assertIn('href="/tr/collaborate"', page)


if __name__ == "__main__":
    unittest.main()
