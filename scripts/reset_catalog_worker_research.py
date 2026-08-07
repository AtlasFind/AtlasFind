"""Recoverably reset only catalog-worker research data, never the public catalog."""
from __future__ import annotations

import argparse
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESEARCH_FILES = (
    "overnight-tool-candidates.json", "catalog-worker-records.json", "catalog-worker-state.json",
    "catalog-worker-truth-report.json", "catalog-worker-reviews.json", "catalog-worker.stop",
)


def reset_research(root: Path) -> Path:
    research = root / "data/research"
    backup = research / ("reset-backup-" + datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S"))
    backup.mkdir(parents=True, exist_ok=False)
    for name in RESEARCH_FILES:
        source = research / name
        if source.exists():
            shutil.move(str(source), str(backup / name))
    queue = {
        "version": 3, "updated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "status": "research_only", "reset_from_scratch": True, "items": [],
        "stats": {"scanned": 0, "added": 0, "duplicates": 0, "rejected": 0, "errors": 0, "cycles": 0},
    }
    (research / "overnight-tool-candidates.json").write_text(
        json.dumps(queue, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (research / "catalog-worker-reset.json").write_text(json.dumps({
        "reset_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "backup_directory": str(backup), "public_catalog_touched": False,
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return backup


def main() -> None:
    parser = argparse.ArgumentParser(description="Back up and reset AtlasFind catalog-worker research")
    parser.add_argument("--yes", action="store_true")
    args = parser.parse_args()
    if not args.yes:
        raise SystemExit("Add --yes to confirm the recoverable research-only reset")
    backup = reset_research(ROOT)
    print(f"Research reset completed; backup: {backup}")
    print("Public data/tools.json was not changed")


if __name__ == "__main__":
    main()
