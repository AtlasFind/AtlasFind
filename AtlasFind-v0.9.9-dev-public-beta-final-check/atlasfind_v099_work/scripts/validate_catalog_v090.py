"""Validate the AtlasFind v0.9.0 expanded catalog and icon metadata."""
from __future__ import annotations
import json
import sys
from collections import Counter
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tool_schema import validate_tools

tools = json.loads((ROOT / "data" / "tools.json").read_text(encoding="utf-8"))
translations = json.loads((ROOT / "data" / "tool_translations_tr_v090.json").read_text(encoding="utf-8"))
errors = validate_tools(tools)

if len(tools) < 600:
    errors.append(f"catalog must contain at least 600 tools, found {len(tools)}")
for index, tool in enumerate(tools):
    icon = tool.get("icon_url")
    if not isinstance(icon, str) or not icon.startswith("https://"):
        errors.append(f"tools[{index}].icon_url must be an https URL")
    if not tool.get("icon_alt"):
        errors.append(f"tools[{index}].icon_alt is required")
    website = tool.get("website", "")
    if not urlparse(website).netloc:
        errors.append(f"tools[{index}].website is invalid")

ids = {tool["id"] for tool in tools}
translated_ids = {row.get("tool_id") for row in translations}
missing_translation_targets = sorted(translated_ids - ids)
if missing_translation_targets:
    errors.append(f"translation rows target missing tools: {missing_translation_targets[:10]}")

categories = Counter(tool["category"] for tool in tools)
if len(categories) < 15:
    errors.append(f"catalog needs at least 15 categories, found {len(categories)}")

if errors:
    print("Catalog validation failed:")
    for error in errors[:200]:
        print(f"- {error}")
    raise SystemExit(1)

print(f"Catalog validation successful: {len(tools)} tools, {len(categories)} categories, {len(translations)} new Turkish translations and icons for every listing.")
