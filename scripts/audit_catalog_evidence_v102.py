"""Generate a machine-readable and Markdown evidence audit for v1.0.2."""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from catalog.evidence import audit_evidence, publication_ready
from catalog.loader import load_catalog


def main() -> None:
    tools = load_catalog(validate=True)
    rows = []
    codes = Counter()
    ready_count = 0
    for tool in tools:
        ready, issues = publication_ready(tool)
        ready_count += int(ready)
        codes.update(issue.code for issue in issues)
        rows.append({
            "id": tool.get("id"),
            "slug": tool.get("slug"),
            "name": tool.get("name"),
            "publication_ready": ready,
            "issues": [issue.__dict__ for issue in issues],
        })

    reports = ROOT / "reports"
    reports.mkdir(exist_ok=True)
    json_path = reports / "catalog-evidence-v102.json"
    md_path = reports / "catalog-evidence-v102.md"
    payload = {
        "total_records": len(tools),
        "publication_ready": ready_count,
        "not_ready": len(tools) - ready_count,
        "issue_counts": dict(codes),
        "records": rows,
    }
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# AtlasFind v1.0.2 Evidence Audit",
        "",
        f"- Total records: {len(tools)}",
        f"- Strict publication-ready: {ready_count}",
        f"- Requires evidence work: {len(tools) - ready_count}",
        "",
        "## Issue totals",
        "",
    ]
    lines.extend(f"- `{code}`: {count}" for code, count in sorted(codes.items()))
    lines.extend(["", "## First 100 records requiring work", ""])
    for row in [item for item in rows if not item["publication_ready"]][:100]:
        issue_codes = ", ".join(issue["code"] for issue in row["issues"])
        lines.append(f"- `{row['slug']}`: {issue_codes}")
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Evidence audit complete: {ready_count}/{len(tools)} records pass the strict publication gate")
    print(f"Reports: {json_path.relative_to(ROOT)}, {md_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
