"""Apply the reviewed 150-tool expansion only after every release gate passes."""
from __future__ import annotations

import hashlib
import json
import sys
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tool_schema import validate_tools

CATALOG = ROOT / "data/tools.json"
STAGING = ROOT / "data/research/manual-expansion-850-records.json"
SOURCE_AUDIT = ROOT / "reports/manual-expansion-850-source-audit.json"
LOGO_AUDIT = ROOT / "reports/manual-expansion-850-logo-import.json"
TAXONOMY = ROOT / "data/taxonomies/categories.json"
CATALOG_DIR = ROOT / "data/catalog"
MANIFEST = CATALOG_DIR / "manifest.json"


def fail(message: str) -> None:
    raise SystemExit(f"Release gate failed: {message}")


def domain(value: str) -> str:
    return urlparse(value).netloc.lower().removeprefix("www.")


def main() -> None:
    current = json.loads(CATALOG.read_text(encoding="utf-8"))
    additions = json.loads(STAGING.read_text(encoding="utf-8"))
    source_audit = json.loads(SOURCE_AUDIT.read_text(encoding="utf-8"))
    logo_audit = json.loads(LOGO_AUDIT.read_text(encoding="utf-8"))
    categories = set(json.loads(TAXONOMY.read_text(encoding="utf-8"))["values"])

    if len(current) not in {700, 850}:
        fail(f"expected the reviewed 700-tool base or an idempotent 850-tool rerun, found {len(current)}")
    current = current[:700]
    if len(additions) != 150:
        fail(f"expected 150 staged tools, found {len(additions)}")
    if [tool.get("id") for tool in additions] != list(range(701, 851)):
        fail("staged IDs must be exactly 701..850")
    if source_audit.get("checked") != 300 or source_audit.get("failed") != 0:
        fail("all 300 official website/repository checks must pass")
    if logo_audit.get("verified") != 150 or logo_audit.get("fallback") != 0:
        fail("all 150 tools must have a verified official logo")

    old_slugs = {tool["slug"].casefold() for tool in current}
    old_names = {tool["name"].strip().casefold() for tool in current}
    old_domains = {domain(tool.get("website", "")) for tool in current if domain(tool.get("website", ""))}
    for tool in additions:
        if tool["slug"].casefold() in old_slugs or tool["name"].strip().casefold() in old_names:
            fail(f"duplicate catalog identity: {tool['name']}")
        website_domain = domain(tool.get("website", ""))
        if website_domain and website_domain in old_domains:
            fail(f"duplicate official website domain: {website_domain}")
        if tool.get("category") not in categories:
            fail(f"unknown category for {tool['slug']}: {tool.get('category')}")
        logo = (tool.get("branding") or {}).get("logo") or {}
        if logo.get("status") != "verified" or not logo.get("local_path"):
            fail(f"unverified logo: {tool['slug']}")
        logo_path = ROOT / logo["local_path"]
        if not logo_path.is_file():
            fail(f"missing local logo: {logo_path}")
        checksum = hashlib.sha256(logo_path.read_bytes()).hexdigest()
        if checksum != logo.get("checksum"):
            fail(f"logo checksum mismatch: {tool['slug']}")

        tool["verification"] = {
            "status": "verified",
            "date": date.today().isoformat(),
            "note": "Identity, official website, source repository, license, taxonomy and official logo passed the controlled AtlasFind 850 expansion review.",
        }
        tool["quality_status"] = "verified"
        tool["quality_review"] = {
            "scope": "manual-850-expansion",
            "reviewed_at": date.today().isoformat(),
            "note": "Schema, duplicate identity/domain, 300 live sources, taxonomy and 150 local official logos passed release gates.",
        }
        tool["publication_status"] = "published"

    merged = current + additions
    errors = validate_tools(merged)
    if errors:
        fail("schema errors: " + " | ".join(errors[:10]))
    if len({tool["id"] for tool in merged}) != 850 or len({tool["slug"].casefold() for tool in merged}) != 850:
        fail("merged catalog IDs/slugs are not unique")

    CATALOG.write_text(json.dumps(merged, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    STAGING.write_text(json.dumps(additions, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    file_by_category = {path.stem.replace("-", " ").title(): path.name for path in CATALOG_DIR.glob("*.json")
                        if path.name != "manifest.json"}
    # Preserve canonical category spellings from the existing files, including AI.
    for file_name in manifest["files"]:
        path = CATALOG_DIR / file_name
        rows = json.loads(path.read_text(encoding="utf-8"))
        if rows:
            file_by_category[rows[0]["category"]] = file_name
    for category in categories:
        file_name = file_by_category.get(category)
        if not file_name:
            fail(f"no category catalog file for {category}")
        rows = [tool for tool in merged if tool["category"] == category]
        (CATALOG_DIR / file_name).write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    manifest["record_count"] = 850
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"catalog_tools": len(merged), "added": len(additions), "logos_verified": 150,
                      "live_sources_passed": 300, "categories": len({tool['category'] for tool in merged})}))


if __name__ == "__main__":
    main()
