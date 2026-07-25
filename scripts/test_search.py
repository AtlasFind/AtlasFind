from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from search_engine import rank_tools

TOOLS = json.loads((ROOT / "data" / "tools.json").read_text(encoding="utf-8"))

CASES = [
    ("photosop", {"gimp", "photopea", "krita", "adobe-photoshop"}),
    ("ücretsiz photoshop alternatifi", {"gimp", "photopea", "krita"}),
    ("eski bilgisayar için video editörü", {"shotcut", "openshot", "kdenlive"}),
    ("internetsiz yapay zeka", {"ollama", "lm-studio", "jan", "anythingllm"}),
    ("bedava kod editörü windows", {"visual-studio-code", "notepad-plus-plus", "zed"}),
    ("açık kaynak tarayıcı", {"firefox", "brave"}),
]

failures = []
for query, expected in CASES:
    ranked, meta = rank_tools(TOOLS, query)
    top = [item["tool"]["slug"] for item in ranked[:8]]
    if not expected.intersection(top):
        failures.append(f"{query!r}: expected one of {sorted(expected)}, got {top}")
    print(f"{query} -> {top[:5]} | corrected={meta['corrected_query']}")

if failures:
    print("\nSearch test failures:")
    for failure in failures:
        print(f"- {failure}")
    raise SystemExit(1)
print(f"\nSearch tests successful: {len(CASES)} queries passed.")
