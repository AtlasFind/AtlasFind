"""Create portable AtlasFind catalog-worker review and import packages."""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from tool_schema import validate_tools


def timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")


def desktop_directory() -> Path:
    user = Path.home()
    for candidate in (user / "OneDrive" / "Desktop", user / "Desktop"):
        if candidate.is_dir():
            return candidate
    return user / "Desktop"


def _write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _packed(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def _checksum(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _create_database(path: Path, records: list[dict[str, Any]]) -> None:
    db = sqlite3.connect(path)
    try:
        db.executescript("""
        PRAGMA journal_mode=DELETE; PRAGMA foreign_keys=ON;
        CREATE TABLE export_info (key TEXT PRIMARY KEY, value TEXT NOT NULL);
        CREATE TABLE tools (id INTEGER NOT NULL, slug TEXT PRIMARY KEY, name TEXT NOT NULL,
          description TEXT NOT NULL, purpose TEXT NOT NULL, category TEXT NOT NULL, subcategory TEXT NOT NULL,
          website TEXT NOT NULL, pricing TEXT NOT NULL, publication_status TEXT NOT NULL,
          review_decision TEXT NOT NULL, quality_status TEXT NOT NULL, icon_url TEXT NOT NULL, raw_json TEXT NOT NULL);
        CREATE TABLE features (tool_slug TEXT NOT NULL, position INTEGER NOT NULL, value TEXT NOT NULL,
          PRIMARY KEY(tool_slug,position), FOREIGN KEY(tool_slug) REFERENCES tools(slug));
        CREATE TABLE platforms (tool_slug TEXT NOT NULL, position INTEGER NOT NULL, value TEXT NOT NULL,
          PRIMARY KEY(tool_slug,position), FOREIGN KEY(tool_slug) REFERENCES tools(slug));
        CREATE TABLE sources (tool_slug TEXT NOT NULL, position INTEGER NOT NULL, label TEXT NOT NULL,
          url TEXT NOT NULL, source_type TEXT NOT NULL, claims_json TEXT NOT NULL,
          PRIMARY KEY(tool_slug,position), FOREIGN KEY(tool_slug) REFERENCES tools(slug));
        CREATE TABLE claim_reviews (tool_slug TEXT NOT NULL, claim TEXT NOT NULL, status TEXT NOT NULL,
          note TEXT NOT NULL, source_types_json TEXT NOT NULL,
          PRIMARY KEY(tool_slug,claim), FOREIGN KEY(tool_slug) REFERENCES tools(slug));
        CREATE TABLE logo_candidates (tool_slug TEXT NOT NULL, position INTEGER NOT NULL, url TEXT NOT NULL,
          source_page TEXT NOT NULL, source_type TEXT NOT NULL, score INTEGER NOT NULL,
          review_status TEXT NOT NULL, raw_json TEXT NOT NULL,
          PRIMARY KEY(tool_slug,position), FOREIGN KEY(tool_slug) REFERENCES tools(slug));
        CREATE TABLE editorial_reviews (tool_slug TEXT PRIMARY KEY, decision TEXT NOT NULL, note TEXT NOT NULL,
          reviewed_at TEXT, reviewed_by TEXT, edits_json TEXT NOT NULL,
          FOREIGN KEY(tool_slug) REFERENCES tools(slug));
        """)
        db.executemany("INSERT INTO export_info VALUES (?,?)", [
            ("schema", "atlasfind-catalog-worker-v1"),
            ("created_at", datetime.now(timezone.utc).isoformat()),
        ])
        for record in records:
            slug, review = str(record["slug"]), record.get("editorial_review") or {}
            db.execute("INSERT INTO tools VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (
                record["id"], slug, record["name"], record["description"], record.get("purpose") or "",
                record["category"], record["subcategory"], record["website"], record["pricing"],
                record.get("publication_status") or "research_only", review.get("decision") or "pending",
                record.get("quality_status") or "unverified", record.get("icon_url") or "", _packed(record)))
            for table, values in (("features", record.get("features") or []), ("platforms", record.get("platforms") or [])):
                db.executemany(f"INSERT INTO {table} VALUES (?,?,?)", [(slug, i, str(v)) for i, v in enumerate(values)])
            for i, source in enumerate(record.get("source_references") or []):
                db.execute("INSERT INTO sources VALUES (?,?,?,?,?,?)", (slug, i, source.get("label") or "", source.get("url") or "", source.get("type") or "", _packed(source.get("claims") or [])))
            metadata = record.get("research_metadata") or {}
            for claim, value in (metadata.get("claim_review") or {}).items():
                db.execute("INSERT INTO claim_reviews VALUES (?,?,?,?,?)", (slug, claim, value.get("status") or "unknown", value.get("note") or "", _packed(value.get("source_types") or [])))
            for i, logo in enumerate((metadata.get("logo_review") or {}).get("candidates") or []):
                db.execute("INSERT INTO logo_candidates VALUES (?,?,?,?,?,?,?,?)", (slug, i, logo.get("url") or "", logo.get("source_page") or "", logo.get("source_type") or "", int(logo.get("score") or 0), logo.get("review_status") or "pending", _packed(logo)))
            db.execute("INSERT INTO editorial_reviews VALUES (?,?,?,?,?,?)", (slug, review.get("decision") or "pending", review.get("note") or "", review.get("reviewed_at"), review.get("reviewed_by"), _packed(review.get("edits") or {})))
        db.commit()
        if db.execute("PRAGMA integrity_check").fetchone() != ("ok",):
            raise ValueError("SQLite integrity check failed")
    finally:
        db.close()


def create_export_package(records: list[dict[str, Any]], destination_root: Path | None = None) -> dict[str, Any]:
    """Export all review data plus a schema-valid, approved-only import file."""
    root = destination_root or desktop_directory()
    root.mkdir(parents=True, exist_ok=True)
    token, suffix = timestamp(), 0
    while True:
        tail = f"-{suffix}" if suffix else ""
        final = root / f"AtlasFind-Katalog-Export-{token}{tail}"
        staging = root / f".AtlasFind-Katalog-Export-{token}{tail}.building"
        if not final.exists() and not staging.exists():
            break
        suffix += 1
    staging.mkdir()
    try:
        approved = []
        for source in records:
            if (source.get("editorial_review") or {}).get("decision") == "approved_for_export":
                record = dict(source)
                record.pop("editorial_review", None)
                record["publication_status"] = "pending_review"
                approved.append(record)
        errors = validate_tools(approved)
        if errors:
            raise ValueError("Approved records are not AtlasFind-compatible: " + "; ".join(errors[:10]))
        ready = staging / "atlasfind-tools-ready.json"
        review = staging / "atlasfind-review-records.json"
        database = staging / "atlasfind-catalog-review.sqlite3"
        report = staging / "atlasfind-export-report.json"
        _write_json(ready, approved)
        _write_json(review, records)
        _create_database(database, records)
        decisions: dict[str, int] = {}
        for record in records:
            decision = (record.get("editorial_review") or {}).get("decision") or "pending"
            decisions[decision] = decisions.get(decision, 0) + 1
        _write_json(report, {"created_at": datetime.now(timezone.utc).isoformat(), "total_records": len(records),
                             "ready_for_import": len(approved), "decisions": decisions,
                             "automatic_publication": False, "catalog_schema_errors": errors})
        files = [ready, review, database, report]
        _write_json(staging / "atlasfind-export-manifest.json", {
            "format": "atlasfind-catalog-export-v1", "created_at": datetime.now(timezone.utc).isoformat(),
            "files": [{"name": p.name, "bytes": p.stat().st_size, "sha256": _checksum(p)} for p in files],
        })
        os.replace(staging, final)
        archive = Path(shutil.make_archive(str(final), "zip", root_dir=final))
        return {"directory": str(final), "archive": str(archive), "total": len(records), "ready": len(approved)}
    except Exception:
        shutil.rmtree(staging, ignore_errors=True)
        raise
