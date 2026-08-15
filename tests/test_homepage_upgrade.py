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
            self.assertIn('class="hero-proof hero-confidence-line"', page)
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

    def test_homepage_keeps_familiar_featured_order_and_compact_filters(self):
        page = self.client.get("/tr/").get_data(as_text=True)
        positions = [page.index(f">{name}<") for name in ("ChatGPT", "Claude", "Gemini", "Perplexity")]
        self.assertEqual(positions, sorted(positions))
        self.assertIn('class="filter-panel home-filter-panel"', page)
        self.assertNotIn('class="filter-panel home-filter-panel is-open"', page)
        self.assertNotIn("catalog.price_Ã¼cretsiz", page)

    def test_header_has_one_more_menu_with_utility_links(self):
        page = self.client.get("/tr/").get_data(as_text=True)
        self.assertEqual(page.count('id="menuButton"'), 1)
        self.assertEqual(page.count('id="moreNavigation"'), 1)
        self.assertIn('aria-controls="moreNavigation"', page)
        self.assertNotIn('id="primaryNavigation"', page)
        self.assertIn("Hakkımızda", page)
        self.assertIn("Puanlama", page)

    def test_collections_are_below_core_discovery_sections(self):
        page = self.client.get("/tr/").get_data(as_text=True)
        self.assertLess(page.index('id="tools"'), page.index('id="discovery-hub"'))
        self.assertLess(page.index('id="categories"'), page.index('id="discovery-hub"'))

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
