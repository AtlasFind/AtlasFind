"""Synthetic scalability benchmark for catalog validation, lookup and filtering."""

from __future__ import annotations

import copy
import statistics
import sys
from pathlib import Path
from time import perf_counter

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from catalog.loader import load_catalog
from catalog.validator import validate_catalog
from search_engine import rank_tools


def clone_catalog(base: list[dict], target: int) -> list[dict]:
    generated: list[dict] = []
    for index in range(target):
        tool = copy.deepcopy(base[index % len(base)])
        tool["id"] = index + 1
        tool["slug"] = f"{tool['slug']}-benchmark-{index + 1}"
        tool["name"] = f"{tool['name']} Benchmark {index + 1}"
        tool["website"] = f"https://benchmark-{index + 1}.example.com"
        generated.append(tool)
    return generated


def measure(callback, repeats=3):
    samples=[]
    for _ in range(repeats):
        started=perf_counter(); callback(); samples.append((perf_counter()-started)*1000)
    return statistics.median(samples)


def main() -> None:
    base = load_catalog(validate=True)[:100]
    print("count,validation_ms,index_ms,filter_ms,search_ms")
    for count in (100, 1000, 5000, 10000):
        tools = clone_catalog(base, count)
        validation_ms = measure(lambda: validate_catalog(tools), 1)
        index_ms = measure(lambda: {tool["slug"]: tool for tool in tools})
        filter_ms = measure(lambda: [tool for tool in tools if "web" in tool.get("platforms", [])])
        search_ms = measure(lambda: rank_tools(tools, "free code editor"), 1)
        print(f"{count},{validation_ms:.2f},{index_ms:.2f},{filter_ms:.2f},{search_ms:.2f}")


if __name__ == "__main__":
    main()
