"""Deterministic and cacheable loader for category-based AtlasFind catalog files."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Iterable

from .validator import CatalogValidationError, validate_catalog

ROOT = Path(__file__).resolve().parents[1]
CATALOG_DIR = ROOT / "data" / "catalog"
MANIFEST_PATH = CATALOG_DIR / "manifest.json"


class CatalogLoadError(RuntimeError):
    """Raised when catalog files cannot be loaded safely."""


def _safe_catalog_path(relative_path: str) -> Path:
    candidate = (CATALOG_DIR / relative_path).resolve()
    catalog_root = CATALOG_DIR.resolve()
    if candidate == catalog_root or catalog_root not in candidate.parents:
        raise CatalogLoadError(f"Unsafe catalog path: {relative_path!r}")
    if candidate.suffix.lower() != ".json":
        raise CatalogLoadError(f"Catalog entries must be JSON files: {relative_path!r}")
    return candidate


def _read_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise CatalogLoadError(f"Catalog file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise CatalogLoadError(f"Invalid JSON in {path}: line {exc.lineno}, column {exc.colno}") from exc


def _manifest_signature() -> tuple:
    if not MANIFEST_PATH.exists():
        return ("missing",)
    manifest = _read_json(MANIFEST_PATH)
    files = manifest.get("files", []) if isinstance(manifest, dict) else []
    signature = [(str(MANIFEST_PATH), MANIFEST_PATH.stat().st_mtime_ns, MANIFEST_PATH.stat().st_size)]
    for item in files:
        if not isinstance(item, str):
            continue
        path = _safe_catalog_path(item)
        if path.exists():
            stat = path.stat()
            signature.append((str(path), stat.st_mtime_ns, stat.st_size))
        else:
            signature.append((str(path), -1, -1))
    return tuple(signature)


@lru_cache(maxsize=4)
def _load_catalog_cached(signature: tuple, validate: bool) -> tuple[dict, ...]:
    del signature
    manifest = _read_json(MANIFEST_PATH)
    if not isinstance(manifest, dict):
        raise CatalogLoadError("Catalog manifest must be a JSON object")
    file_names = manifest.get("files")
    if not isinstance(file_names, list) or not file_names:
        raise CatalogLoadError("Catalog manifest must contain a non-empty 'files' list")

    tools: list[dict] = []
    for relative_path in file_names:
        if not isinstance(relative_path, str) or not relative_path.strip():
            raise CatalogLoadError("Manifest file entries must be non-empty strings")
        path = _safe_catalog_path(relative_path)
        payload = _read_json(path)
        if not isinstance(payload, list):
            raise CatalogLoadError(f"Catalog file must contain a JSON array: {path}")
        for item in payload:
            if not isinstance(item, dict):
                raise CatalogLoadError(f"Catalog records must be objects: {path}")
            tools.append(item)

    if validate:
        errors = validate_catalog(tools)
        if errors:
            raise CatalogValidationError(errors)
    return tuple(tools)


def load_catalog(*, validate: bool = True) -> list[dict]:
    """Load all catalog records in manifest order."""
    return [dict(item) for item in _load_catalog_cached(_manifest_signature(), validate)]


def load_published_catalog(*, validate: bool = True) -> list[dict]:
    """Load only records explicitly allowed to appear on the public site."""
    return [tool for tool in load_catalog(validate=validate) if tool.get("publication_status", "published") == "published"]


def iter_catalog_files() -> Iterable[Path]:
    manifest = _read_json(MANIFEST_PATH)
    for relative_path in manifest.get("files", []):
        yield _safe_catalog_path(relative_path)
