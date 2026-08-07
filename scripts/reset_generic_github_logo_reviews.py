"""Reset approved generic GitHub assets so the strengthened brand guard can reject them."""

from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
QUEUE = ROOT / "data" / "research" / "catalog-expansion-logo-queue.json"


def main() -> None:
    payload = json.loads(QUEUE.read_text(encoding="utf-8"))
    reset = 0
    for item in payload["items"]:
        for candidate in item.get("candidates", []):
            host = (urlparse(str(candidate.get("url") or "")).hostname or "").lower()
            path = urlparse(str(candidate.get("url") or "")).path.lower()
            if candidate.get("review_status") == "approved" and "githubassets.com" in host and "app-icon" in path:
                candidate["review_status"] = "pending"
                candidate.pop("reviewed_at", None)
                candidate.pop("reviewed_by", None)
                reset += 1
    QUEUE.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Reset {reset} generic GitHub approval(s)")


if __name__ == "__main__":
    main()
