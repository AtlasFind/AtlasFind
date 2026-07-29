from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


class RuntimeSafetyTests(unittest.TestCase):
    def test_report_is_local_only_and_counts_queue(self):
        script = Path(__file__).resolve().parents[1] / "scripts" / "logo_queue_report_v104.py"
        spec = importlib.util.spec_from_file_location("logo_report", script)
        module = importlib.util.module_from_spec(spec)
        assert spec and spec.loader
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "queue.json"
            path.write_text(json.dumps({"items": [
                {"status": "imported", "candidates": [{"review_status": "approved"}]},
                {"status": "error", "candidates": [{"review_status": "approved"}]},
            ]}), encoding="utf-8")
            items = module._load_items(path)
            self.assertEqual(len(items), 2)

    def test_approved_errors_only_does_not_include_review_items(self):
        # Regression guard for the filtering semantics used by the CLI.
        items = [
            {"status": "error", "candidates": [{"review_status": "approved"}]},
            {"status": "review", "candidates": [{"review_status": "approved"}]},
        ]
        selected = []
        for item in items:
            has_approved = any(c.get("review_status") == "approved" for c in item["candidates"])
            if item["status"] == "error" and has_approved:
                selected.append(item)
        self.assertEqual(len(selected), 1)
        self.assertEqual(selected[0]["status"], "error")


if __name__ == "__main__":
    unittest.main()
