import json
import shutil
import sqlite3
import unittest
from datetime import date
from pathlib import Path

from services.catalog_worker_export_service import create_export_package
from services.catalog_worker_record_service import build_review_record


class CatalogWorkerExportTests(unittest.TestCase):
    def setUp(self):
        self.root = Path("work/catalog-export-test-output").resolve()
        if self.root.exists():
            shutil.rmtree(self.root)
        self.root.mkdir(parents=True)

    def tearDown(self):
        if self.root.exists():
            shutil.rmtree(self.root)

    def record(self):
        record = build_review_record({
            "slug": "sample-app", "name": "Sample App",
            "description_source_text": "A detailed official description of the sample application for testing.",
            "category_suggestion": "Productivity", "subcategory_suggestion": "Task Management",
            "official_url": "https://sample.example", "repository": "sample/app",
            "repository_url": "https://github.com/sample/app", "license": "MIT", "stars": 1000,
        }, 701, today=date(2026, 8, 8))
        record["purpose"] = "Helps teams organize tasks."
        record["features"] = ["Task boards"]
        record["editorial_review"] = {"decision": "approved_for_export", "note": "Checked", "edits": {}}
        return record

    def test_creates_json_sqlite_manifest_and_zip(self):
        result = create_export_package([self.record()], self.root)
        folder, archive = Path(result["directory"]), Path(result["archive"])
        self.assertTrue(archive.is_file())
        ready = json.loads((folder / "atlasfind-tools-ready.json").read_text(encoding="utf-8"))
        self.assertEqual("pending_review", ready[0]["publication_status"])
        manifest = json.loads((folder / "atlasfind-export-manifest.json").read_text(encoding="utf-8"))
        self.assertEqual("atlasfind-catalog-export-v1", manifest["format"])
        db = sqlite3.connect(folder / "atlasfind-catalog-review.sqlite3")
        try:
            self.assertEqual(1, db.execute("SELECT COUNT(*) FROM tools").fetchone()[0])
            self.assertEqual(1, db.execute("SELECT COUNT(*) FROM features").fetchone()[0])
            self.assertEqual("ok", db.execute("PRAGMA integrity_check").fetchone()[0])
        finally:
            db.close()

    def test_unapproved_records_remain_in_review_db_but_not_ready_json(self):
        record = self.record()
        record["editorial_review"]["decision"] = "pending"
        result = create_export_package([record], self.root)
        folder = Path(result["directory"])
        self.assertEqual([], json.loads((folder / "atlasfind-tools-ready.json").read_text(encoding="utf-8")))
        db = sqlite3.connect(folder / "atlasfind-catalog-review.sqlite3")
        try:
            self.assertEqual(1, db.execute("SELECT COUNT(*) FROM tools").fetchone()[0])
        finally:
            db.close()


if __name__ == "__main__":
    unittest.main()
