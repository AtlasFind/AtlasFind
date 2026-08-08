import unittest

from app import app, load_tools
from services.catalog_score_service import calculate_catalog_score


class CatalogScoreServiceTests(unittest.TestCase):
    def test_every_tool_has_a_valid_automated_score(self):
        tools = load_tools("en")
        self.assertEqual(len(tools), 1000)
        for tool in tools:
            score = tool.get("catalog_score") or {}
            self.assertEqual(score.get("version"), "1.0.0")
            self.assertTrue(score.get("automated"))
            self.assertIsInstance(score.get("score"), float)
            self.assertGreaterEqual(score["score"], 0)
            self.assertLessEqual(score["score"], 10)
            self.assertEqual(set(score.get("components", {})), {
                "capability", "accessibility", "value", "transparency", "completeness"
            })

    def test_scores_are_deterministic_and_not_uniform(self):
        tools = load_tools("en")
        scores = [tool["catalog_score"]["score"] for tool in tools]
        self.assertGreaterEqual(len(set(scores)), 15)
        sample = tools[0]
        self.assertEqual(calculate_catalog_score(sample), calculate_catalog_score(sample))

    def test_automated_score_does_not_forge_editor_approval(self):
        for tool in load_tools("en"):
            rating = tool.get("rating_v103") or {}
            if not rating.get("publishable"):
                self.assertFalse(rating.get("reviewed_by"))
                self.assertFalse(rating.get("approved_by"))
                self.assertEqual(tool.get("rating_source"), "atlasfind_catalog_v1")

    def test_score_is_visible_on_catalog_detail_and_comparison(self):
        app.config.update(TESTING=True)
        with app.test_client() as client:
            catalog = client.get("/en/tools")
            self.assertEqual(catalog.status_code, 200)
            self.assertIn(b"/ 10", catalog.data)
            detail = client.get("/en/tools/chatgpt")
            self.assertEqual(detail.status_code, 200)
            self.assertIn(b"AtlasFind automated catalog score", detail.data)
            comparison = client.get("/en/compare?left=chatgpt&right=claude")
            self.assertEqual(comparison.status_code, 200)
            self.assertIn(b"/ 10", comparison.data)


if __name__ == "__main__":
    unittest.main()
