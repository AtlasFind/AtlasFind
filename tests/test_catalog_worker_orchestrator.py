import json
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import catalog_worker_orchestrator as orchestrator


class CatalogWorkerOrchestratorTests(unittest.TestCase):
    def setUp(self):
        self.records = Path("work/test-orchestrator-records.json")
        self.state = Path("work/test-orchestrator-state.json")
        self.records.unlink(missing_ok=True)
        self.state.unlink(missing_ok=True)

    def tearDown(self):
        self.records.unlink(missing_ok=True)
        self.state.unlink(missing_ok=True)

    def candidate(self):
        return {"slug": "sample", "name": "Sample", "description_source_text": "A detailed official sample application description.",
                "category_suggestion": "Productivity", "subcategory_suggestion": "Tasks",
                "official_url": "https://sample.example", "repository": "sample/app",
                "repository_url": "https://github.com/sample/app", "license": "MIT", "stars": 500}

    def test_materialize_checkpoints_and_preserves_logo_progress(self):
        previous = [{"slug": "sample", "research_metadata": {"logo_review": {"status": "candidates_found", "candidates": [{"url": "https://sample.example/logo.png"}]}}}]
        self.records.write_text(json.dumps(previous), encoding="utf-8")
        state = {"cycles": 0, "errors": 0, "retries": {}}
        with patch.object(orchestrator, "RECORDS", self.records), patch.object(orchestrator, "STATE", self.state):
            records = orchestrator.materialize({"items": [self.candidate()]}, [], state)
        self.assertEqual("candidates_found", records[0]["research_metadata"]["logo_review"]["status"])
        saved_state = json.loads(self.state.read_text(encoding="utf-8"))
        self.assertEqual("records_built", saved_state["phase"])


if __name__ == "__main__":
    unittest.main()
