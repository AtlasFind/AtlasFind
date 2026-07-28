from __future__ import annotations

import json
import py_compile
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run_script(relative_path: str) -> None:
    path = ROOT / relative_path
    result = subprocess.run(
        [sys.executable, str(path)],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )
    if result.stdout:
        print(result.stdout.rstrip())
    if result.returncode:
        if result.stderr:
            print(result.stderr.rstrip(), file=sys.stderr)
        raise RuntimeError(f"Failed: {relative_path}")


def compile_python() -> int:
    count = 0
    ignored = {".venv", "__pycache__"}
    for path in ROOT.rglob("*.py"):
        if any(part in ignored for part in path.parts):
            continue
        py_compile.compile(str(path), doraise=True)
        count += 1
    return count


def verify_catalog_counts() -> tuple[int, int, int]:
    manifest_path = ROOT / "data" / "catalog" / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    records = []
    for item in manifest["files"]:
        filename = item["path"] if isinstance(item, dict) else item
        path = ROOT / "data" / "catalog" / filename
        payload = json.loads(path.read_text(encoding="utf-8"))
        records.extend(payload.get("tools", payload) if isinstance(payload, dict) else payload)

    verified = sum(
        1 for tool in records
        if tool.get("verification", {}).get("status") == "verified"
    )
    pending = sum(
        1 for tool in records
        if tool.get("verification", {}).get("status") == "pending"
    )
    return len(records), verified, pending


def optional_flask_smoke_test() -> None:
    try:
        import flask  # noqa: F401
    except ModuleNotFoundError:
        print("Flask smoke test skipped: install requirements.txt first.")
        return

    sys.path.insert(0, str(ROOT))
    from app import app

    app.config.update(TESTING=True)
    with app.test_client() as client:
        for route in ("/tr/", "/en/", "/health", "/ready"):
            response = client.get(route)
            if response.status_code != 200:
                raise RuntimeError(
                    f"Smoke test failed: {route} returned {response.status_code}"
                )
    print("Flask smoke test successful: TR, EN, health and ready routes return 200.")


def main() -> None:
    print("AtlasFind v1.0.2 release validation")
    print("=" * 39)

    compiled = compile_python()
    print(f"Python syntax successful: {compiled} files")

    for script in (
        "scripts/validate_catalog_v102.py",
        "scripts/build_catalog.py",
        "scripts/audit_catalog_evidence_v102.py",
        "scripts/validate_localization_v101.py",
        "scripts/validate_tools.py",
        "scripts/validate_content.py",
        "scripts/validate_security.py",
    ):
        run_script(script)

    total, verified, pending = verify_catalog_counts()
    if total != 600 or verified != 5 or pending != 595:
        raise RuntimeError(
            "Unexpected catalog state: "
            f"total={total}, verified={verified}, pending={pending}"
        )

    optional_flask_smoke_test()
    print("=" * 39)
    print(
        "Release validation successful: "
        f"{total} tools, {verified} strict verified, {pending} pending."
    )


if __name__ == "__main__":
    main()
