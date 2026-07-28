from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from recommendation_engine import recommend_tools

TOOLS = json.loads((ROOT / "data" / "tools.json").read_text(encoding="utf-8"))
CASES = [
    ({"purpose":"coding","platform":"windows","budget":"free","hardware":"light","experience":"beginner","privacy":"open-source","offline":True}, {"visual-studio-code","notepad-plus-plus"}),
    ({"purpose":"privacy","platform":"linux","budget":"free","hardware":"heavy","experience":"advanced","privacy":"open-source","offline":True}, {"keepassxc","veracrypt","librewolf","ollama"}),
    ({"purpose":"video","platform":"windows","budget":"paid","hardware":"heavy","experience":"advanced","privacy":"any","offline":False}, {"davinci-resolve","vegas-pro","obs-studio"}),
    ({"purpose":"writing","platform":"web","budget":"freemium","hardware":"any","experience":"beginner","privacy":"any","offline":False}, {"chatgpt","claude","perplexity","notion"}),
]

failures = []
for profile, expected in CASES:
    results = recommend_tools(TOOLS, profile, limit=8)
    top = [item["tool"]["slug"] for item in results]
    if not expected.intersection(top[:5]):
        failures.append(f"{profile['purpose']}: expected one of {sorted(expected)} in top 5, got {top[:5]}")
    if results and not results[0]["reasons"]:
        failures.append(f"{profile['purpose']}: top recommendation has no positive explanation")
    print(f"{profile['purpose']} -> {top[:5]}")

if failures:
    print("\nRecommendation quality test failures:")
    for failure in failures:
        print(f"- {failure}")
    raise SystemExit(1)
print(f"\nRecommendation quality tests successful: {len(CASES)} profiles passed.")
