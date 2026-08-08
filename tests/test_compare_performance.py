import unittest

from app import app


class ComparePerformanceTests(unittest.TestCase):
    def setUp(self):
        app.config.update(TESTING=True)
        self.client = app.test_client()

    def test_empty_compare_page_starts_with_categories_not_four_thousand_options(self):
        body = self.client.get("/tr/compare").get_data(as_text=True)
        self.assertIn('name="category"', body)
        self.assertNotIn("data-compare-tool-select", body)
        self.assertLess(len(body), 100_000)

    def test_selected_category_only_renders_tools_from_that_category(self):
        body = self.client.get("/tr/compare?category=artificial-intelligence").get_data(as_text=True)
        self.assertEqual(body.count("data-compare-tool-select"), 4)
        self.assertIn('value="chatgpt"', body)
        self.assertNotIn('value="7-zip"', body)
