import unittest
from datetime import date

from services.catalog_worker_record_service import build_review_record, build_review_records
from tool_schema import validate_tool, validate_tools


class CatalogWorkerRecordTests(unittest.TestCase):
    def candidate(self, **changes):
        value = {
            "slug": "sample-app",
            "name": "Sample App",
            "description_source_text": "A sufficiently detailed official repository description for testing.",
            "category_suggestion": "Productivity",
            "subcategory_suggestion": "Task Management",
            "official_url": "https://sample.example",
            "repository": "sample/sample-app",
            "repository_url": "https://github.com/sample/sample-app",
            "stars": 2500,
            "license": "MIT",
            "topics": ["tasks", "productivity"],
            "discovered_at": "2026-08-08T01:00:00+00:00",
            "discovery_query": "productivity app",
        }
        value.update(changes)
        return value

    def test_record_matches_catalog_schema_but_stays_non_public(self):
        record = build_review_record(self.candidate(), 701, today=date(2026, 8, 8))
        self.assertEqual([], validate_tool(record, 0))
        self.assertEqual("research_only", record["publication_status"])
        self.assertEqual("unverified", record["quality_status"])
        self.assertEqual([], record["features"])
        self.assertIn("official_avatar_required", record["research_metadata"]["publication_blockers"])
        self.assertEqual("missing", record["research_metadata"]["claim_review"]["avatar"]["status"])

    def test_ids_are_deterministic_and_duplicate_slugs_are_skipped(self):
        catalog = [{"id": 700, "slug": "existing"}]
        candidates = [self.candidate(), self.candidate(name="Duplicate"), self.candidate(slug="another", name="Another")]
        records = build_review_records(candidates, catalog, today=date(2026, 8, 8))
        self.assertEqual([701, 702], [item["id"] for item in records])
        self.assertEqual(["sample-app", "another"], [item["slug"] for item in records])
        self.assertEqual([], validate_tools(records))

    def test_github_preview_is_not_promoted_to_official_avatar(self):
        record = build_review_record(self.candidate(image_url="https://opengraph.githubassets.com/x/y"), 701)
        self.assertNotIn("opengraph.githubassets.com", record["icon_url"])
        self.assertEqual("local-generated", record["icon_source"])

    def test_strong_topics_correct_the_discovery_category(self):
        record = build_review_record(self.candidate(topics=["password-manager", "privacy"]), 701)
        self.assertEqual("Cybersecurity", record["category"])
        self.assertEqual("Security and Privacy", record["subcategory"])


if __name__ == "__main__":
    unittest.main()
