import unittest
from unittest.mock import patch

from services.catalog_worker_logo_service import discover_worker_logo_candidates, rank_worker_logo_candidates


class CatalogWorkerLogoTests(unittest.TestCase):
    def test_rejects_social_cards_and_foreign_domains(self):
        candidates = [
            {"url": "https://tool.example/social.png", "relation": "og:image", "score": 100},
            {"url": "https://cdn.other.example/logo.png", "relation": "icon", "score": 120},
            {"url": "https://tool.example/app-icon.png", "relation": "manifest-icon", "score": 130},
        ]
        result = rank_worker_logo_candidates("https://tool.example", candidates)
        self.assertEqual(["https://tool.example/app-icon.png"], [item["url"] for item in result])
        self.assertFalse(result[0]["auto_publish_allowed"])

    @patch("services.catalog_worker_logo_service.discover_logo_candidates")
    def test_official_candidates_always_require_human_selection(self, discover):
        discover.return_value = ([{
            "url": "https://tool.example/logo.svg", "source_page": "https://tool.example",
            "source_type": "official_product_site", "relation": "icon", "score": 110,
        }], [{"status": "success"}])
        review = discover_worker_logo_candidates({"website": "https://tool.example", "source_references": []})
        self.assertEqual("candidates_found", review["status"])
        self.assertTrue(review["requires_human_selection"])
        self.assertIsNone(review["selected_candidate"])
        self.assertEqual("pending_human_review", review["candidates"][0]["review_status"])

    def test_low_confidence_candidate_is_not_kept(self):
        result = rank_worker_logo_candidates("https://tool.example", [{
            "url": "https://tool.example/favicon.ico", "relation": "icon", "score": 40,
        }])
        self.assertEqual([], result)

    def test_official_page_may_declare_a_cdn_asset(self):
        result = rank_worker_logo_candidates("https://tool.example", [{
            "url": "https://assets.cdn.example/tool-logo.png", "source_page": "https://tool.example/",
            "relation": "manifest-icon", "score": 125,
        }])
        self.assertEqual("declared_by_official_page", result[0]["brand_match_status"])


if __name__ == "__main__":
    unittest.main()
