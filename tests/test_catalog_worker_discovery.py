import json
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import atlas_catalog_worker as worker


class CatalogWorkerDiscoveryTests(unittest.TestCase):
    def setUp(self):
        self.catalog = Path("work/test-discovery-catalog.json")
        self.catalog.write_text("[]", encoding="utf-8")

    def tearDown(self):
        self.catalog.unlink(missing_ok=True)

    def test_rotating_page_is_sent_to_github_search(self):
        queue = {"items": [], "stats": {"scanned": 0, "added": 0, "duplicates": 0, "rejected": 0, "errors": 0, "cycles": 0}}
        with patch.object(worker, "CATALOG", self.catalog), patch.object(worker, "write_json"), \
             patch.object(worker.time, "sleep"), patch.object(worker, "SEARCHES", [("query", "Category", "Sub")]), \
             patch.object(worker, "github_get", return_value={"items": []}) as github:
            worker.discover_once(queue, per_query=10, min_stars=250, max_candidates=0, page=4)
        self.assertEqual(4, github.call_args.args[1]["page"])


if __name__ == "__main__": unittest.main()
