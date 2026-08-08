import hashlib
import json
import unittest
from pathlib import Path

from tool_schema import validate_tools


ROOT = Path(__file__).resolve().parents[1]


class ManualExpansion850Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tools = json.loads((ROOT / "data/tools.json").read_text(encoding="utf-8"))
        cls.additions = cls.tools[700:]

    def test_catalog_is_exactly_850_unique_schema_valid_tools(self):
        self.assertEqual(850, len(self.tools))
        self.assertEqual(850, len({tool["id"] for tool in self.tools}))
        self.assertEqual(850, len({tool["slug"].casefold() for tool in self.tools}))
        self.assertEqual([], validate_tools(self.tools))

    def test_all_150_additions_are_published_and_logo_verified(self):
        self.assertEqual(list(range(701, 851)), [tool["id"] for tool in self.additions])
        for tool in self.additions:
            self.assertEqual("verified", tool["verification"]["status"], tool["slug"])
            self.assertEqual("verified", tool["quality_status"], tool["slug"])
            self.assertEqual("published", tool["publication_status"], tool["slug"])
            logo = tool["branding"]["logo"]
            self.assertEqual("verified", logo["status"], tool["slug"])
            path = ROOT / logo["local_path"]
            self.assertTrue(path.is_file(), tool["slug"])
            self.assertEqual(logo["checksum"], hashlib.sha256(path.read_bytes()).hexdigest(), tool["slug"])

    def test_release_audits_are_complete(self):
        sources = json.loads((ROOT / "reports/manual-expansion-850-source-audit.json").read_text(encoding="utf-8"))
        logos = json.loads((ROOT / "reports/manual-expansion-850-logo-import.json").read_text(encoding="utf-8"))
        self.assertEqual((300, 300, 0), (sources["checked"], sources["passed"], sources["failed"]))
        self.assertEqual((150, 150, 0), (logos["total"], logos["verified"], logos["fallback"]))


if __name__ == "__main__":
    unittest.main()
