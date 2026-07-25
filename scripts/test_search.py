from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from search_engine import rank_tools

TOOLS = json.loads((ROOT / "data" / "tools.json").read_text(encoding="utf-8"))
CASES = json.loads((ROOT / "data" / "search_test_cases.json").read_text(encoding="utf-8"))

failures = []
for case in CASES:
    query = case["query"]
    ranked, meta = rank_tools(TOOLS, query)
    top_k = int(case.get("top_k", 5))
    top = [item["tool"]["slug"] for item in ranked[:top_k]]
    expected = set(case.get("expected_slugs", []))
    forbidden = set(case.get("must_not_include", []))
    if expected and not expected.intersection(top):
        failures.append(f"{query!r}: expected one of {sorted(expected)} in top {top_k}, got {top}")
    bad = forbidden.intersection(top)
    if bad:
        failures.append(f"{query!r}: forbidden results appeared in top {top_k}: {sorted(bad)}")
    if ranked and not ranked[0].get("reasons"):
        failures.append(f"{query!r}: top result has no match explanation")
    print(f"{query} -> {top} | corrected={meta['corrected_query']}")

if failures:
    print("\nSearch quality test failures:")
    for failure in failures:
        print(f"- {failure}")
    raise SystemExit(1)
print(f"\nSearch quality tests successful: {len(CASES)} cases passed.")
