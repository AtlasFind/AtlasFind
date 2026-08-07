"""Long-running, review-first discovery worker for new AtlasFind candidates.

The worker only reads public GitHub metadata and writes a local research queue.
It never publishes tools, downloads executables, or edits the public catalog.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "data/tools.json"
QUEUE = ROOT / "data/research/overnight-tool-candidates.json"
LOG = ROOT / "logs/catalog-worker.log"

SEARCHES = [
    ("productivity app", "Productivity", "Productivity"),
    ("time tracking app", "Productivity", "Time Tracking"),
    ("note taking app", "Office and Documents", "Note Taking"),
    ("developer tool", "Development", "Developer Tools"),
    ("database client", "Development", "Database Tools"),
    ("self hosted dashboard", "Web and Hosting", "Self-Hosted Platforms"),
    ("privacy security tool", "Cybersecurity", "Privacy Tools"),
    ("backup sync app", "Cloud and Storage", "Backup and Sync"),
    ("communication chat app", "Communication", "Team Communication"),
    ("audio editor", "Audio and Music", "Audio Editing"),
    ("video editor", "Video and Animation", "Video Editing"),
    ("design tool", "Design and Graphics", "Design Tools"),
    ("browser privacy", "Browsers and Internet", "Privacy Browsers"),
    ("marketing analytics", "Marketing and SEO", "Marketing Analytics"),
    ("finance budget app", "Finance and Business", "Budgeting"),
    ("game launcher", "Gaming and Entertainment", "Game Launchers"),
]


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def slugify(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.casefold()).strip("-")


def domain(url: str) -> str:
    return urlparse(url).netloc.casefold().removeprefix("www.")


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def log(message: str) -> None:
    line = f"[{now()}] {message}"
    print(line, flush=True)
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a", encoding="utf-8") as handle:
        handle.write(line + "\n")


def github_get(path: str, params: dict[str, object]) -> dict:
    url = "https://api.github.com" + path + "?" + urlencode(params)
    headers = {"User-Agent": "AtlasFind-catalog-worker", "Accept": "application/vnd.github+json"}
    token = os.environ.get("GITHUB_TOKEN", "").strip()
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = Request(url, headers=headers)
    with urlopen(request, timeout=25) as response:
        return json.loads(response.read().decode("utf-8"))


def load_queue() -> dict:
    if QUEUE.exists():
        queue = json.loads(QUEUE.read_text(encoding="utf-8"))
    else:
        queue = {"version": 2, "updated_at": now(), "status": "research_only", "items": []}
    queue["version"] = 2
    queue.setdefault("stats", {"scanned": 0, "added": len(queue["items"]), "duplicates": 0, "rejected": 0, "errors": 0, "cycles": 0})
    for item in queue["items"]:
        item.setdefault("image_url", f'https://opengraph.githubassets.com/atlasfind-catalog-worker/{item["repository"]}')
    return queue


def discover_once(queue: dict, *, per_query: int, min_stars: int, max_candidates: int) -> int:
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    known_slugs = {tool["slug"] for tool in catalog}
    known_domains = {domain(tool["website"]) for tool in catalog}
    queued_repos = {item["repository"].casefold() for item in queue["items"]}
    added = 0
    stats = queue["stats"]
    for query, category, subcategory in SEARCHES:
        if max_candidates and len(queue["items"]) >= max_candidates:
            break
        try:
            result = github_get(
                "/search/repositories",
                {"q": f'{query} stars:>={min_stars} archived:false fork:false', "sort": "stars", "order": "desc", "per_page": per_query},
            )
        except HTTPError as exc:
            stats["errors"] += 1
            log(f"GitHub search paused ({exc.code}) for query: {query}")
            if exc.code in {403, 429}:
                time.sleep(65)
            continue
        except (URLError, TimeoutError, json.JSONDecodeError) as exc:
            stats["errors"] += 1
            log(f"Search error for {query}: {exc}")
            continue
        for repo in result.get("items", []):
            stats["scanned"] += 1
            repository = str(repo.get("full_name") or "")
            name = str(repo.get("name") or "").replace("_", " ").replace("-", " ").strip()
            slug = slugify(name)
            homepage = str(repo.get("homepage") or "").strip()
            official_url = homepage if homepage.startswith("https://") else str(repo.get("html_url") or "")
            if not repository or not slug or not official_url.startswith("https://"):
                stats["rejected"] += 1
                continue
            if repository.casefold() in queued_repos or slug in known_slugs or domain(official_url) in known_domains:
                stats["duplicates"] += 1
                continue
            description = str(repo.get("description") or "").strip()
            if len(description) < 20:
                stats["rejected"] += 1
                continue
            item = {
                "slug": slug,
                "name": name.title(),
                "description_source_text": description,
                "category_suggestion": category,
                "subcategory_suggestion": subcategory,
                "official_url": official_url,
                "repository": repository,
                "repository_url": repo.get("html_url"),
                "stars": int(repo.get("stargazers_count") or 0),
                "license": (repo.get("license") or {}).get("spdx_id"),
                "topics": repo.get("topics") or [],
                "image_url": f"https://opengraph.githubassets.com/atlasfind-catalog-worker/{repository}",
                "logo_status": "needs_official_asset_review",
                "verification_status": "pending_human_review",
                "publication_status": "research_only",
                "discovered_at": now(),
                "discovery_query": query,
            }
            queue["items"].append(item)
            queued_repos.add(repository.casefold())
            added += 1
            stats["added"] += 1
            if max_candidates and len(queue["items"]) >= max_candidates:
                break
        queue["updated_at"] = now()
        write_json(QUEUE, queue)
        time.sleep(7 if os.environ.get("GITHUB_TOKEN") else 12)
    return added


def main() -> None:
    parser = argparse.ArgumentParser(description="Discover review-only AtlasFind tool candidates")
    parser.add_argument("--hours", type=float, default=8.0)
    parser.add_argument("--max-candidates", type=int, default=300)
    parser.add_argument("--per-query", type=int, default=20)
    parser.add_argument("--min-stars", type=int, default=500)
    parser.add_argument("--cycle-minutes", type=int, default=45)
    parser.add_argument("--once", action="store_true", help="Run one discovery cycle and exit")
    args = parser.parse_args()
    if not 0 <= args.max_candidates <= 100000:
        raise SystemExit("--max-candidates must be 0 (unlimited) or between 1 and 100000")
    queue = load_queue()
    deadline = None if args.hours <= 0 else time.monotonic() + max(0.05, args.hours) * 3600
    log(f"Worker started: target={args.max_candidates}, hours={args.hours}, existing={len(queue['items'])}")
    while (deadline is None or time.monotonic() < deadline) and (not args.max_candidates or len(queue["items"]) < args.max_candidates):
        added = discover_once(queue, per_query=args.per_query, min_stars=args.min_stars, max_candidates=args.max_candidates)
        queue["stats"]["cycles"] += 1
        log(f"Cycle complete: added={added}, queued={len(queue['items'])}")
        if args.once or (args.max_candidates and len(queue["items"]) >= args.max_candidates):
            break
        time.sleep(max(1, args.cycle_minutes) * 60)
    queue["updated_at"] = now()
    queue["last_run_completed_at"] = now()
    write_json(QUEUE, queue)
    log(f"Worker finished safely: queued={len(queue['items'])}; nothing auto-published")


if __name__ == "__main__":
    main()
