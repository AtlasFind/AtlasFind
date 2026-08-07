import unittest

from services.catalog_worker_enrichment_service import extract_readme_evidence


README = """
# Sample App

Sample App helps teams organize projects and keep daily work visible in one place.

## Features

- Shared task boards
- Offline-first editing
- Markdown notes with full-text search

## Installation

Download installers for Windows, macOS and Linux from the releases page.

Sample App is free and open-source software.
"""


class CatalogWorkerEnrichmentTests(unittest.TestCase):
    def test_extracts_supported_purpose_features_and_platforms(self):
        evidence = extract_readme_evidence(README)
        self.assertTrue(evidence["purpose"].startswith("Sample App helps teams"))
        self.assertEqual(["Shared task boards", "Offline-first editing", "Markdown notes with full-text search"], [item["text"] for item in evidence["features"]])
        self.assertEqual(["Windows", "macOS", "Linux"], evidence["platforms"])
        self.assertEqual("free", evidence["pricing"]["pricing_type"])

    def test_does_not_treat_random_platform_mentions_as_support(self):
        evidence = extract_readme_evidence("# Tool\n\nA useful tool with enough description for reviewers.\n\n## Community\nSomeone mentioned Windows here.")
        self.assertEqual([], evidence["platforms"])

    def test_ignores_code_blocks_and_images(self):
        evidence = extract_readme_evidence("# Tool\n\nA useful tool with enough description for reviewers.\n\n## Features\n```\n- fake command\n```\n![logo](x.png)")
        self.assertEqual([], evidence["features"])


if __name__ == "__main__":
    unittest.main()
