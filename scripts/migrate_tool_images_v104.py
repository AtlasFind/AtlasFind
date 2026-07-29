from __future__ import annotations
import json
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from services.image_service import normalize_branding

FILES = [ROOT / "data" / "tools.json", *sorted((ROOT / "data" / "catalog").glob("*.json"))]


def migrate(path: Path) -> int:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        return 0
    changed = 0
    for tool in payload:
        normalized = normalize_branding(tool)
        if tool.get("branding") != normalized:
            tool["branding"] = normalized
            changed += 1
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return changed


def main() -> None:
    total = 0
    for path in FILES:
        if path.is_file():
            changed = migrate(path)
            total += changed
            print(f"{path.relative_to(ROOT)}: {changed} records migrated")
    print(f"AtlasFind v1.0.4 image metadata migration complete: {total} record updates")

if __name__ == "__main__":
    main()
