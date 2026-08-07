import json
import shutil
import unittest
from pathlib import Path

from scripts.reset_catalog_worker_research import reset_research


class CatalogWorkerResetTests(unittest.TestCase):
    def setUp(self):
        self.root = Path("work/test-catalog-reset").resolve()
        if self.root.exists(): shutil.rmtree(self.root)
        (self.root / "data/research").mkdir(parents=True)
        (self.root / "data/tools.json").write_text('[{"slug":"public-tool"}]', encoding="utf-8")
        (self.root / "data/research/overnight-tool-candidates.json").write_text('{"items":[{"slug":"old"}]}', encoding="utf-8")
        (self.root / "data/research/catalog-worker-records.json").write_text('[{"slug":"old"}]', encoding="utf-8")

    def tearDown(self):
        if self.root.exists(): shutil.rmtree(self.root)

    def test_reset_backs_up_research_and_preserves_public_catalog(self):
        backup = reset_research(self.root)
        self.assertTrue((backup / "catalog-worker-records.json").is_file())
        queue = json.loads((self.root / "data/research/overnight-tool-candidates.json").read_text(encoding="utf-8"))
        self.assertEqual([], queue["items"])
        self.assertIn("public-tool", (self.root / "data/tools.json").read_text(encoding="utf-8"))


if __name__ == "__main__": unittest.main()
