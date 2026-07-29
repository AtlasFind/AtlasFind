from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from catalog.loader import load_catalog
from services.logo_import_service import import_approved_logo


def _same_site(candidate_url: str, official_url: str) -> bool:
    left = (urlparse(candidate_url).hostname or "").lower().removeprefix("www.")
    right = (urlparse(official_url).hostname or "").lower().removeprefix("www.")
    return bool(left and right) and (
        left == right or left.endswith("." + right) or right.endswith("." + left)
    )


def _candidate_priority(candidate: dict, official_url: str) -> tuple:
    relation = str(candidate.get("relation") or "").lower()
    relation_rank = 0
    if "apple-touch-icon" in relation:
        relation_rank = 4
    elif "manifest" in relation:
        relation_rank = 3
    elif "icon" in relation:
        relation_rank = 2
    elif "og:image" in relation:
        relation_rank = 1
    return (
        1 if _same_site(str(candidate.get("url") or ""), official_url) else 0,
        relation_rank,
        int(candidate.get("score") or 0),
    )


def _eligible_candidates(item: dict, tool: dict, try_alternates: bool) -> list[dict]:
    candidates = list(item.get("candidates") or [])
    approved = [c for c in candidates if c.get("review_status") == "approved"]
    if not try_alternates:
        return approved[:1]

    official_url = str(tool.get("website") or tool.get("official_url") or "")
    alternates = []
    for candidate in candidates:
        if candidate in approved or candidate.get("review_status") == "rejected":
            continue
        relation = str(candidate.get("relation") or "").lower()
        score = int(candidate.get("score") or 0)
        same_site = _same_site(str(candidate.get("url") or ""), official_url)
        if not same_site:
            continue
        if "icon" not in relation and "manifest" not in relation:
            continue
        if score < 80:
            continue
        alternates.append(candidate)
    alternates.sort(key=lambda c: _candidate_priority(c, official_url), reverse=True)
    return approved + alternates


def _write_catalog_changes(tools: dict[str, dict], changed: set[str]) -> None:
    catalog_dir = ROOT / "data" / "catalog"
    for file in catalog_dir.glob("*.json"):
        if file.name == "manifest.json":
            continue
        data = json.loads(file.read_text(encoding="utf-8"))
        rows = data.get("tools", data) if isinstance(data, dict) else data
        dirty = False
        for index, row in enumerate(rows):
            if row.get("slug") in changed:
                rows[index] = tools[row["slug"]]
                dirty = True
        if dirty:
            file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Import approved AtlasFind logo candidates.")
    parser.add_argument("--queue", default="data/branding/logo-queue.json")
    parser.add_argument("--verified-by", required=True)
    parser.add_argument("--limit", type=int, default=100)
    parser.add_argument("--timeout", type=int, default=8, help="Per-candidate network timeout in seconds.")
    parser.add_argument("--max-candidates-per-tool", type=int, default=5)
    parser.add_argument("--approved-errors-only", action="store_true", help="Retry only error tools that already contain an approved candidate.")
    parser.add_argument("--checkpoint-every", type=int, default=1, help="Persist queue/catalog progress after this many processed tools.")
    parser.add_argument("--retry-errors", action="store_true")
    parser.add_argument(
        "--try-alternates",
        action="store_true",
        help="When the approved candidate fails, try high-confidence same-site icon candidates.",
    )
    args = parser.parse_args()

    path = ROOT / args.queue
    payload = json.loads(path.read_text(encoding="utf-8"))
    items = payload.get("items", []) if isinstance(payload, dict) else payload
    tools = {tool["slug"]: tool for tool in load_catalog()}
    changed: set[str] = set()
    processed = 0
    failures = 0
    skipped_imported = 0
    skipped_not_approved = 0

    for item in items:
        if processed >= args.limit:
            break
        status = item.get("status")
        if status == "imported":
            skipped_imported += 1
            continue
        if status == "error" and not args.retry_errors:
            continue
        if args.approved_errors_only:
            has_approved = any(
                isinstance(c, dict) and c.get("review_status") == "approved"
                for c in (item.get("candidates") or [])
            )
            if status != "error" or not has_approved:
                continue

        tool = tools.get(item.get("slug"))
        if not tool:
            item["status"] = "error"
            item["last_error"] = "Tool not found"
            failures += 1
            continue

        candidates = _eligible_candidates(item, tool, args.try_alternates)
        candidates = candidates[: max(1, args.max_candidates_per_tool)]
        if not candidates:
            skipped_not_approved += 1
            continue

        errors: list[str] = []
        imported = False
        for candidate in candidates:
            original_status = candidate.get("review_status")
            if original_status != "approved":
                candidate["review_status"] = "approved"
                candidate["auto_selected_for_retry"] = True
            try:
                tool["branding"] = import_approved_logo(
                    tool,
                    candidate,
                    verified_by=args.verified_by,
                    timeout_seconds=max(2, args.timeout),
                )
                item["status"] = "imported"
                item["last_error"] = None
                item["imported_candidate_url"] = candidate.get("url")
                candidate["import_status"] = "imported"
                changed.add(tool["slug"])
                imported = True
                print(f"Imported: {tool['slug']} <- {candidate.get('url')}")
                break
            except Exception as exc:
                message = str(exc)
                errors.append(f"{candidate.get('url')}: {message}")
                candidate["import_status"] = "failed"
                candidate["import_error"] = message
                if original_status != "approved":
                    candidate["review_status"] = original_status or "pending"

        if not imported:
            item["status"] = "error"
            item["last_error"] = " | ".join(errors[-5:])
            failures += 1
            print(f"ERROR {item.get('slug')}: all {len(candidates)} eligible candidate(s) failed")

        processed += 1
        if args.checkpoint_every > 0 and processed % args.checkpoint_every == 0:
            _write_catalog_changes(tools, changed)
            path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"Checkpoint saved: processed={processed}, imported={len(changed)}, failures={failures}")

    _write_catalog_changes(tools, changed)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(
        "Logo import complete: "
        f"imported={len(changed)}, failures={failures}, "
        f"skipped_imported={skipped_imported}, "
        f"skipped_not_approved={skipped_not_approved}"
    )
    return 1 if failures and not changed else 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("\nImport stopped by user. The most recent checkpoint remains saved.")
        raise SystemExit(130)
