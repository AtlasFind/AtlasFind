"""Release validation for the AtlasFind v1.0.2 modular catalog."""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from catalog.loader import MANIFEST_PATH, iter_catalog_files, load_catalog


def main() -> None:
    tools = load_catalog(validate=True)
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    files = list(iter_catalog_files())
    if manifest.get("record_count") != len(tools):
        raise SystemExit("Manifest record_count does not match the loaded catalog")
    if len(files) != len(set(files)):
        raise SystemExit("Manifest contains duplicate file paths")

    statuses = Counter(tool.get("verification", {}).get("status") for tool in tools)
    publications = Counter(tool.get("publication_status", "published") for tool in tools)
    sourced = sum(bool(tool.get("source_references")) for tool in tools)
    print(f"v1.0.2 catalog validation successful: {len(tools)} tools in {len(files)} files")
    print(f"Verification states: {dict(statuses)}")
    print(f"Publication states: {dict(publications)}")
    print(f"Records with source references: {sourced}/{len(tools)}")
    if sourced == 0:
        print("NOTICE: legacy catalog records are structurally migrated but not yet evidence-verified.")


if __name__ == "__main__":
    main()
