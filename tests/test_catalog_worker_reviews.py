import json
import unittest
from pathlib import Path

from services.catalog_worker_review_service import collection_completeness, export_readiness, load_reviews, merge_reviews, save_review


class CatalogWorkerReviewTests(unittest.TestCase):
    def setUp(self):
        self.path = Path("work/test-catalog-worker-reviews.json")
        self.path.unlink(missing_ok=True)

    def tearDown(self):
        self.path.unlink(missing_ok=True)

    def test_review_edits_are_persisted_without_publication(self):
        saved = save_review("sample", {"decision": "approved_for_export", "note": "Checked", "edits": {"purpose": "A reviewed purpose"}}, path=self.path)
        self.assertFalse(saved["auto_publish_allowed"])
        merged = merge_reviews([{"slug": "sample", "purpose": "Old"}], load_reviews(self.path))
        self.assertEqual("A reviewed purpose", merged[0]["purpose"])
        self.assertEqual("approved_for_export", merged[0]["editorial_review"]["decision"])

    def test_unknown_edits_are_rejected(self):
        with self.assertRaises(ValueError):
            save_review("sample", {"edits": {"publication_status": "published"}}, path=self.path)

    def test_invalid_feature_values_are_rejected(self):
        with self.assertRaises(ValueError):
            save_review("sample", {"edits": {"features": [""]}}, path=self.path)

    def test_export_readiness_blocks_incomplete_or_unverified_records(self):
        blockers = export_readiness({
            "name": "Sample", "description": "Description", "purpose": "Purpose",
            "category": "Development", "subcategory": "Tools", "website": "https://example.com",
            "features": ["Feature"], "source_references": [{"url": "https://example.com"}],
            "research_metadata": {"missing_claims": ["pricing"], "logo_review": {"status": "candidates_found"}},
        })
        self.assertTrue(any("pricing" in item for item in blockers))
        self.assertTrue(any("avatar" in item.casefold() for item in blockers))

    def test_export_readiness_accepts_complete_verified_record(self):
        blockers = export_readiness({
            "name": "Sample", "description": "Description", "purpose": "Purpose",
            "category": "Development", "subcategory": "Tools", "website": "https://example.com",
            "features": ["Feature"], "source_references": [{"url": "https://example.com"}],
            "research_metadata": {"missing_claims": [], "logo_review": {"status": "verified_official_asset"}},
        })
        self.assertEqual([], blockers)

    def test_raw_candidate_is_not_shown_as_complete_tool(self):
        result = collection_completeness({"name": "Raw", "description": "Description", "category": "Other",
                                          "subcategory": "Other", "website": "https://example.com",
                                          "research_metadata": {"claim_review": {}, "logo_review": {}}})
        self.assertFalse(result["complete"])
        self.assertIn("purpose", result["missing"])
        self.assertIn("avatar", result["missing"])

    def test_evidence_complete_candidate_enters_complete_list(self):
        result = collection_completeness({
            "name": "Ready", "description": "Description", "purpose": "Purpose", "category": "Development",
            "subcategory": "Tools", "website": "https://example.com", "features": ["Feature"],
            "source_references": [{"url": "https://example.com"}],
            "research_metadata": {"claim_review": {name: {"status": "provisionally_supported"} for name in
                                ("purpose", "features", "pricing", "platforms")},
                                "logo_review": {"status": "candidates_found", "candidates": [{"url": "https://example.com/logo.png"}]}}
        })
        self.assertTrue(result["complete"])
        self.assertEqual(100, result["percent"])


if __name__ == "__main__":
    unittest.main()
