"""Concurrent live-source audit for the fixed 150-tool expansion."""
from __future__ import annotations

import json
import ssl
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
RECORDS = ROOT / "data/research/manual-expansion-850-records.json"
REPORT = ROOT / "reports/manual-expansion-850-source-audit.json"


def check(url: str) -> dict:
    request = Request(url, headers={"User-Agent": "AtlasFindEditorialReview/1.0", "Accept": "text/html,application/json,*/*;q=0.5"})
    try:
        with urlopen(request, timeout=20, context=ssl.create_default_context()) as response:
            response.read(1024)
            return {"url": url, "ok": 200 <= response.status < 400, "status": response.status,
                    "final_url": response.geturl(), "content_type": response.headers.get_content_type()}
    except HTTPError as exc:
        # Bot-protected official pages still prove that the domain is live.
        return {"url": url, "ok": exc.code in {401, 403, 405, 429}, "status": exc.code,
                "final_url": exc.geturl(), "error": str(exc)}
    except (URLError, TimeoutError, OSError) as exc:
        return {"url": url, "ok": False, "status": None, "error": f"{type(exc).__name__}: {exc}"}


def main() -> None:
    records = json.loads(RECORDS.read_text(encoding="utf-8"))
    jobs = [(record["slug"], kind, url) for record in records for kind, url in
            (("website", record["website"]), ("repository", record["source_references"][1]["url"]))]
    results = []
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(check, url): (slug, kind) for slug, kind, url in jobs}
        for future in as_completed(futures):
            slug, kind = futures[future]
            results.append({"slug": slug, "kind": kind, **future.result()})
    results.sort(key=lambda item: (item["slug"], item["kind"]))
    failures = [item for item in results if not item["ok"]]
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps({"generated_at": datetime.now(timezone.utc).isoformat(),
        "checked": len(results), "passed": len(results)-len(failures), "failed": len(failures),
        "results": results}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"checked": len(results), "passed": len(results)-len(failures), "failed": len(failures)}))


if __name__ == "__main__": main()
