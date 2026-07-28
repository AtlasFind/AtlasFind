from pathlib import Path
import statistics
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app import app, load_tools, load_articles


def measure(label, fn, rounds=10):
    samples = []
    for _ in range(rounds):
        start = time.perf_counter()
        fn()
        samples.append((time.perf_counter() - start) * 1000)
    print(f"{label}: median={statistics.median(samples):.2f} ms min={min(samples):.2f} ms max={max(samples):.2f} ms")


with app.test_request_context('/tr/'):
    measure('load_tools(tr)', lambda: load_tools('tr'))
    measure('load_articles(tr)', lambda: load_articles('tr'))

client = app.test_client()
for path in ('/en/', '/tr/', '/en/tools/gimp', '/tr/tools/gimp', '/sitemap.xml'):
    measure(path, lambda p=path: client.get(p), rounds=5)
