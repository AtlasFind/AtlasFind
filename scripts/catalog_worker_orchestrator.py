"""Resumable end-to-end controller for the AtlasFind catalog worker."""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.atlas_catalog_worker import discover_once, load_queue, write_json
from services.catalog_worker_enrichment_service import enrich_candidate
from services.catalog_worker_logo_service import discover_worker_logo_candidates
from services.catalog_worker_record_service import build_review_records
from services.catalog_worker_truth_service import audit_records
from tool_schema import validate_tools

CATALOG = ROOT / "data/tools.json"
QUEUE = ROOT / "data/research/overnight-tool-candidates.json"
RECORDS = ROOT / "data/research/catalog-worker-records.json"
STATE = ROOT / "data/research/catalog-worker-state.json"
TRUTH = ROOT / "data/research/catalog-worker-truth-report.json"
STOP = ROOT / "data/research/catalog-worker.stop"


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def load_state() -> dict:
    if STATE.exists():
        state = json.loads(STATE.read_text(encoding="utf-8"))
    else:
        state = {"version": 1, "cycles": 0, "enrichment_cursor": 0, "logo_cursor": 0,
                 "errors": 0, "retries": {}, "phase": "idle", "created_at": now()}
    state["resumed_at"] = now()
    return state


def checkpoint(state: dict, phase: str, **updates: object) -> None:
    state.update(updates)
    state["phase"] = phase
    state["updated_at"] = now()
    write_json(STATE, state)


def should_stop() -> bool:
    return STOP.exists()


def materialize(queue: dict, catalog: list[dict], state: dict) -> list[dict]:
    records = build_review_records(queue.get("items", []), catalog)
    previous = {}
    if RECORDS.exists():
        previous = {record.get("slug"): record for record in json.loads(RECORDS.read_text(encoding="utf-8"))}
    for record in records:
        old_logo = (previous.get(record.get("slug"), {}).get("research_metadata") or {}).get("logo_review")
        if old_logo and old_logo.get("status") != "not_started":
            record["research_metadata"]["logo_review"] = old_logo
    errors = validate_tools(records)
    if errors:
        raise ValueError("Record schema validation failed: " + "; ".join(errors[:20]))
    write_json(RECORDS, records)
    checkpoint(state, "records_built", records=len(records))
    return records


def enrich_batch(queue: dict, state: dict, size: int, pause: float) -> int:
    items, completed = queue.get("items", []), 0
    start = min(int(state.get("enrichment_cursor", 0)), len(items))
    for index in range(start, len(items)):
        if completed >= size or should_stop():
            break
        item = items[index]
        if item.get("enrichment_status") != "evidence_collected":
            items[index] = enrich_candidate(item)
            if items[index].get("enrichment_status") == "retry_required":
                key = items[index].get("slug", str(index))
                state["retries"][key] = int(state["retries"].get(key, 0)) + 1
                state["errors"] = int(state.get("errors", 0)) + 1
            completed += 1
            write_json(QUEUE, queue)
            time.sleep(max(0.2, pause))
        checkpoint(state, "enriching", enrichment_cursor=index + 1)
    if state.get("enrichment_cursor", 0) >= len(items):
        state["enrichment_cursor"] = 0
    return completed


def logo_batch(records: list[dict], state: dict, size: int, pause: float) -> int:
    completed, start = 0, min(int(state.get("logo_cursor", 0)), len(records))
    for index in range(start, len(records)):
        if completed >= size or should_stop():
            break
        review = (records[index].get("research_metadata") or {}).get("logo_review") or {}
        if review.get("status") == "not_started":
            try:
                records[index]["research_metadata"]["logo_review"] = discover_worker_logo_candidates(records[index])
            except Exception as exc:
                records[index]["research_metadata"]["logo_review"] = {
                    "status": "retry_required", "error": f"{type(exc).__name__}: {exc}",
                    "candidates": [], "attempts": [], "requires_human_selection": True, "selected_candidate": None,
                }
                state["errors"] = int(state.get("errors", 0)) + 1
            completed += 1
            write_json(RECORDS, records)
            time.sleep(max(0.2, pause))
        checkpoint(state, "logo_discovery", logo_cursor=index + 1)
    if state.get("logo_cursor", 0) >= len(records):
        state["logo_cursor"] = 0
    return completed


def run_cycle(state: dict, *, offline: bool, enrichment_batch: int, logo_batch_size: int, pause: float) -> dict:
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    queue = load_queue()
    if not offline and not should_stop():
        checkpoint(state, "discovering")
        discover_once(queue, per_query=10, min_stars=250, max_candidates=0)
    if not offline and not should_stop():
        enrich_batch(queue, state, enrichment_batch, pause)
    records = materialize(queue, catalog, state)
    if not offline and not should_stop():
        logo_batch(records, state, logo_batch_size, pause)
        records = json.loads(RECORDS.read_text(encoding="utf-8"))
    report = audit_records(records, catalog)
    write_json(TRUTH, {"generated_at": now(), **report})
    checkpoint(state, "cycle_complete", cycles=int(state.get("cycles", 0)) + 1,
               truth_passed=report["passed"], truth_failed=report["failed"], records=len(records))
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--offline", action="store_true", help="Build and audit without network calls")
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--enrichment-batch", type=int, default=20)
    parser.add_argument("--logo-batch", type=int, default=10)
    parser.add_argument("--pause", type=float, default=2.0)
    parser.add_argument("--cycle-minutes", type=int, default=30)
    args = parser.parse_args()
    if STOP.exists():
        STOP.unlink()
    state = load_state()
    while not should_stop():
        run_cycle(state, offline=args.offline, enrichment_batch=max(1, args.enrichment_batch),
                  logo_batch_size=max(1, args.logo_batch), pause=max(0.2, args.pause))
        if args.once or args.offline:
            break
        for _ in range(max(1, args.cycle_minutes) * 6):
            if should_stop():
                break
            time.sleep(10)
    checkpoint(state, "stopped_safely" if should_stop() else "idle")


if __name__ == "__main__":
    main()
