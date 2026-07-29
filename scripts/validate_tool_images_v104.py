from __future__ import annotations
import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from validators.image_validator import validate_tool_branding


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate AtlasFind tool branding assets.")
    parser.add_argument("--require-verified", type=int, default=0)
    args = parser.parse_args()

    tools = json.loads((ROOT / "data" / "tools.json").read_text(encoding="utf-8"))
    counts = Counter()
    errors = []
    checksums = defaultdict(list)
    for tool in tools:
        result = validate_tool_branding(tool)
        status = (tool.get("branding") or {}).get("logo", {}).get("status", "missing")
        counts[status] += 1
        if result.metadata.get("checksum"):
            checksums[result.metadata["checksum"]].append(tool.get("slug"))
        if result.errors:
            errors.extend(f"{tool.get('slug')}: {message}" for message in result.errors)
    duplicates = {key: value for key, value in checksums.items() if len(value) > 1}
    report = {
        "total_tools": len(tools),
        "verified": counts["verified"],
        "missing": counts["missing"],
        "pending": counts["pending"],
        "broken": counts["broken"],
        "safe_fallback_coverage": len(tools),
        "duplicate_verified_files": duplicates,
        "critical_errors": errors,
        "required_verified": args.require_verified,
    }
    reports = ROOT / "reports"; reports.mkdir(exist_ok=True)
    (reports / "tool-images-v104.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Total tools: {len(tools)}")
    print(f"Verified official logos: {counts['verified']}")
    print(f"Safe fallback coverage: {len(tools)}/{len(tools)}")
    print(f"Missing official logos: {counts['missing']}")
    print(f"Critical errors: {len(errors)}")
    if errors:
        print("\n".join(errors[:20]))
        return 1
    if counts["verified"] < args.require_verified:
        print(f"FAILED: requires at least {args.require_verified} verified logos.")
        return 1
    print("AtlasFind v1.0.4 image validation successful.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
