import unittest
from datetime import date

from services.catalog_worker_record_service import build_review_record
from services.catalog_worker_truth_service import audit_record, audit_records


def candidate():
    return {
        "slug": "sample-app", "name": "Sample App",
        "description_source_text": "A detailed official description for the sample application under review.",
        "category_suggestion": "Productivity", "subcategory_suggestion": "Task Management",
        "official_url": "https://sample.example", "repository": "sample/app",
        "repository_url": "https://github.com/sample/app", "license": "MIT", "stars": 1000,
    }


class CatalogWorkerTruthTests(unittest.TestCase):
    def test_honest_pending_record_passes_accuracy_audit(self):
        record = build_review_record(candidate(), 701, today=date(2026, 8, 8))
        result = audit_record(record)
        self.assertTrue(result["passed"], result["errors"])

    def test_claim_without_matching_source_is_rejected(self):
        record = build_review_record(candidate(), 701)
        record["research_metadata"]["claim_review"]["features"] = {
            "status": "verified", "source_types": ["official-documentation"], "note": "claimed"
        }
        record["features"] = ["Unsupported feature"]
        result = audit_record(record)
        self.assertFalse(result["passed"])
        self.assertTrue(any("absent source" in error for error in result["errors"]))

    def test_source_type_alone_is_not_enough_without_claim_mapping(self):
        record = build_review_record(candidate(), 701)
        record["research_metadata"]["claim_review"]["features"] = {
            "status": "verified", "source_types": ["official-homepage"], "note": "claimed"
        }
        record["features"] = ["Unsupported feature"]
        result = audit_record(record)
        self.assertTrue(any("not listed" in error for error in result["errors"]))

    def test_fake_verified_logo_is_rejected(self):
        record = build_review_record(candidate(), 701)
        record["research_metadata"]["logo_review"] = {"status": "verified_official_asset", "selected_candidate": {}}
        self.assertTrue(any("checksum" in error for error in audit_record(record)["errors"]))

    def test_public_catalog_and_internal_duplicates_are_rejected(self):
        one = build_review_record(candidate(), 701)
        two = build_review_record({**candidate(), "slug": "second"}, 702)
        report = audit_records([one, two], [{"slug": "existing", "website": "https://public.example"}])
        self.assertEqual(1, report["failed"])
        self.assertTrue(any("Duplicate domain" in error for error in report["results"][1]["errors"]))


if __name__ == "__main__":
    unittest.main()
